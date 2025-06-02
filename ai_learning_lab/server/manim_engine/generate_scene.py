# ai-learning-lab/server/manim_engine/generate_scene.py

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import re

# Import the new prompt adapter
from .prompt_adapter import translate_user_request_to_manim_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Claude system prompt for Manim scene generation
MANIM_SYSTEM_PROMPT = """
You are a Python animation assistant that specializes in Manim Community Edition v0.18+, the mathematical animation library used by 3Blue1Brown.

You are given animation goals or descriptions. Your job is to generate valid Python code using the current Manim Community Library syntax.

**CRITICAL RULES - FOLLOW EXACTLY:**
1. Always define a class that inherits from `Scene` or `MovingCameraScene`
2. Class name must be PascalCase (e.g. `SineCosineComparison`)
3. Always import: `from manim import *`
4. Include `def construct(self):` method and use `.play()`, `.add()`, `.wait()` to animate
5. **NEVER include markdown code fences (```) in your output - only pure Python code**

**AVAILABLE MANIM COMPONENTS (v0.18.1):**

1. Core Scene Classes:
   - Scene
   - MovingCameraScene

2. Basic Shapes and Objects:
   - Circle(radius=float, color=Color)
   - Square(side_length=float, color=Color)
   - Rectangle(height=float, width=float, color=Color)
   - Polygon(*points, fill_opacity=float)
   - Line(start=Point, end=Point, color=Color)
   - Arrow(start=Point, end=Point, color=Color)
   - Dot(point=Point, color=Color)
   - DashedLine(start=Point, end=Point, color=Color)
   - Text(text=str, font_size=float, color=Color)
   - MathTex(tex_string=str, color=Color)

3. Plotting and Graphs:
   - Axes(
       x_range=[start, end, step],
       y_range=[start, end, step],
       x_length=float,
       y_length=float,
       axis_config={
           "include_numbers": bool,
           "numbers_to_include": list,
           "numbers_to_exclude": list,
           "decimal_number_config": {
               "num_decimal_places": int
           }
       }
   )
   - axes.plot(function=lambda x: expression, x_range=[start, end, step], color=Color)
   - axes.plot_parametric_curve(function=lambda t: (x(t), y(t)), t_range=[start, end, step], color=Color)
   - axes.c2p(x, y)  # Convert coordinates to points
   - axes.get_axis_labels(x_label, y_label)  # For axis labels

4. Colors:
   - Basic: RED, GREEN, BLUE, YELLOW, WHITE, BLACK, GRAY, PINK, PURPLE, ORANGE
   - Variants: RED_A, RED_B, RED_C, RED_D, RED_E (same pattern for all basic colors)
   - Special: DARK_BLUE, DARK_BROWN, DARK_GRAY, LIGHT_GRAY, PURE_RED, PURE_GREEN, PURE_BLUE
   - **NEVER use colors like GREEN_DARK, BLUE_DARK, RED_DARK - these don't exist!**
   - **For darker shades, use the _D variant (e.g., GREEN_D instead of GREEN_DARK)**

5. Animation Methods:
   - Create(mobject)
   - Write(mobject)
   - FadeIn(mobject)
   - FadeOut(mobject)
   - Transform(mobject, target_mobject)
   - ReplacementTransform(mobject, target_mobject)
   - GrowFromCenter(mobject)
   - mobject.animate.method()  # For smooth animations

6. Positioning and Movement:
   - Directions: UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR
   - mobject.move_to(point)
   - mobject.shift(vector)
   - mobject.to_edge(direction)
   - mobject.next_to(other_mobject, direction, buff=float)

7. Group Operations:
   - VGroup(*mobjects)  # Group multiple mobjects

8. Scene Control:
   - self.play(*animations, run_time=float)
   - self.wait(duration=float)
   - self.add(*mobjects)

9. Mathematical Constants:
   - PI  # π
   - np.pi  # numpy's π

**CORRECT PLOTTING EXAMPLES:**
```python
# CORRECT way to plot functions in Manim v0.18+
axes = Axes(x_range=[-4, 4], y_range=[-2, 2])
sine_graph = axes.plot(lambda x: np.sin(x), x_range=[-4, 4], color=BLUE)
cosine_graph = axes.plot(lambda x: np.cos(x), x_range=[-4, 4], color=RED)

# CORRECT way to add labels
labels = axes.get_axis_labels(MathTex("x"), MathTex("y"))
sine_label = MathTex("\\sin(x)", color=BLUE).next_to(sine_graph, UP)
cosine_label = MathTex("\\cos(x)", color=RED).next_to(cosine_graph, UP)

# CORRECT way to add points and lines
dot = Dot(axes.c2p(0, 0))
line = Line(axes.c2p(0, 0), axes.c2p(1, 1), color=YELLOW)
```

**IMPORTANT NOTES:**
1. NEVER use `get_x_axis_labels()` or `get_y_axis_labels()` - these don't exist in v0.18.1
2. For axis labels, use `axes.get_axis_labels(x_label, y_label)`
3. For graph labels, use `MathTex()` positioned with `.next_to()`
4. For plotting functions, use `axes.plot()` NOT `axes.get_graph()`
5. For parametric plots, use `axes.plot_parametric_curve()`
6. Always use `axes.c2p(x, y)` to convert coordinates to points
7. Use `VGroup()` to group multiple mobjects
8. Use `self.play()` for animations and `self.wait()` for pauses
9. Use `self.add()` to add objects to the scene without animation
"""

def generate_manim_scene_with_anthropic(prompt: str, api_key: Optional[str] = None) -> str:
    """
    Generates Manim scene code using Anthropic's Claude API.
    
    Args:
        prompt: The animation description prompt
        api_key: Anthropic API key (defaults to CLAUDE_API_KEY environment variable)
        
    Returns:
        Generated Manim Python code
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        logger.error("Anthropic Python SDK not installed. Run: pip install anthropic")
        raise ImportError("Anthropic Python SDK not installed. Run: pip install anthropic")
    
    # Get API key from environment if not provided
    api_key = api_key or os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise ValueError("Anthropic API key not provided and CLAUDE_API_KEY environment variable not set")
    
    # Initialize Anthropic client
    anthropic = Anthropic(api_key=api_key)
    
    try:
        # Call Claude API
        response = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            system=MANIM_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        
        # Extract and return the generated code
        generated_code = response.content[0].text
        
        # Clean up markdown code fences and other artifacts
        generated_code = clean_generated_code(generated_code)
        
        return generated_code.strip()
    
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        raise

def generate_manim_scene_with_openai(prompt: str, api_key: Optional[str] = None) -> str:
    """
    Generates Manim scene code using OpenAI's GPT API.
    
    Args:
        prompt: The animation description prompt
        api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        
    Returns:
        Generated Manim Python code
    """
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("OpenAI Python SDK not installed. Run: pip install openai")
        raise ImportError("OpenAI Python SDK not installed. Run: pip install openai")
    
    # Get API key from environment if not provided
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not provided and OPENAI_API_KEY environment variable not set")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    try:
        # Call GPT API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": MANIM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        # Extract and return the generated code
        generated_code = response.choices[0].message.content
        
        # Clean up markdown code fences and other artifacts
        generated_code = clean_generated_code(generated_code)
        
        return generated_code.strip()
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

def clean_generated_code(code: str) -> str:
    """
    Clean up generated code by removing markdown artifacts and common issues.
    
    Args:
        code: Raw generated code from LLM
        
    Returns:
        Cleaned Python code
    """
    if not code:
        return code
    
    # Remove markdown code fences
    patterns_to_remove = [
        (r'^```python\n', ''),
        (r'^```py\n', ''),
        (r'^```\n', ''),
        (r'\n```$', ''),
        (r'^```python', ''),
        (r'^```py', ''),
        (r'^```', ''),
        (r'```$', ''),
    ]
    
    for pattern, replacement in patterns_to_remove:
        code = re.sub(pattern, replacement, code, flags=re.MULTILINE)
    
    # Remove any remaining triple backticks that might be in the middle
    code = code.replace('```', '')
    
    # Clean up extra whitespace
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip completely empty lines at the beginning and end
        if not cleaned_lines and not line.strip():
            continue
        cleaned_lines.append(line)
    
    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)

# Mock implementation for testing without API
def generate_manim_scene_mock(prompt: str) -> str:
    """
    Mock implementation that returns pre-defined Manim code for testing.
    The prompt here is ALREADY the adapted Manim-specific prompt.
    
    Args:
        prompt: The adapted Manim animation instruction prompt.
        
    Returns:
        Pre-defined Manim Python code
    """
    logger.info(f"Using mock generator with adapted Manim prompt: {prompt}")
    
    # Extract a possible class name from the prompt (less reliable for descriptive prompts)
    # This is a simple heuristic; could be improved or class name could be passed
    words = [word for word in re.findall(r'[A-Za-z]+', prompt) if len(word) > 2 and word.lower() not in ['manim', 'animation', 'scene', 'that', 'shows', 'show', 'create', 'using', 'with']]
    if words:
        class_name = ''.join(word.capitalize() for word in words[:2]) # Take first two significant words
        if not class_name.endswith("Scene"):
             class_name = class_name[:20] # Cap length
    else:
        class_name = "MockAnimatedScene"
    
    # Return a simple template with the prompt as a comment
    return f"""from manim import *

# Generated from prompt: "{prompt}"
class {class_name}(Scene):
    def construct(self):
        # Create a text object with the prompt
        text = MathTex("\\\\text{{Animation: {prompt}}}", font_size=36)
        
        # Animate writing the text
        self.play(Write(text))
        self.wait(1)
        
        # Transform to a different position
        self.play(text.animate.to_edge(UP))
        self.wait(1)
        
        # Create a circle
        circle = Circle(radius=2, color=BLUE)
        
        # Animate drawing the circle
        self.play(Create(circle))
        self.wait(1)
        
        # Fade out
        self.play(FadeOut(text), FadeOut(circle))
        self.wait(0.5)
"""

def generate_manim_scene(user_input: str, use_api: str = "mock") -> Dict[str, Any]:
    """
    High-level function to translate user request, generate Manim scene code using the specified API.
    
    Args:
        user_input: The student's raw question or concept request.
        use_api: Which API to use for Manim code generation ('anthropic', 'openai', or 'mock')
        
    Returns:
        Dictionary containing the generated code, extracted class name, and original user input
    """
    logger.info(f"Received user input: '{user_input[:100]}...'")

    # Step 1: Translate user request to a Manim-specific animation prompt
    # This adapted_prompt is what will be sent to the Manim code generation LLM
    # or used by the mock generator.
    adapted_manim_prompt = translate_user_request_to_manim_prompt(user_input)
    logger.info(f"Adapted Manim prompt: '{adapted_manim_prompt[:100]}...'")

    # Step 2: Generate Manim code using the adapted prompt
    logger.info(f"Generating Manim code with {use_api} API using adapted prompt.")
    if use_api == "anthropic":
        code = generate_manim_scene_with_anthropic(adapted_manim_prompt)
    elif use_api == "openai":
        code = generate_manim_scene_with_openai(adapted_manim_prompt)
    else: # mock
        # The mock generator now also receives the adapted_manim_prompt
        code = generate_manim_scene_mock(adapted_manim_prompt)
    
    # Import the extract_class_name function from save_scene.py
    from .save_scene import extract_class_name
    
    # Extract class name from the generated code
    class_name = extract_class_name(code)
    
    # If class name couldn't be extracted, generate a default name based on the adapted_manim_prompt
    if not class_name:
        # Using adapted_manim_prompt for class name generation might be more specific
        words = [word for word in re.findall(r'[A-Za-z]+', adapted_manim_prompt) if len(word) > 2 and word.lower() not in ['manim', 'animation', 'scene', 'that', 'shows', 'show', 'create', 'using', 'with']]
        if words:
            class_name = ''.join(word.capitalize() for word in words[:2])
            if not class_name.endswith("Scene"):
                class_name = class_name[:20]
        else:
            class_name = "GeneratedScene"
    
    return {
        "code": code,
        "class_name": class_name,
        "original_user_input": user_input, # Keep original for context if needed
        "llm_prompt": adapted_manim_prompt  # Add this for retry mechanism
    }

# Example usage
if __name__ == "__main__":
    student_question = "Can you show me how matrix multiplication works with a 2x2 and a 2x1 matrix?"
    # Test with OpenAI for code generation, which now uses the adapted prompt
    result = generate_manim_scene(student_question, use_api="openai") 
    
    print(f"\n--- Test for: '{student_question}' ---")
    print(f"Adapted Manim Prompt: {result['llm_prompt']}")
    print(f"Generated class: {result['class_name']}")
    print("\nGenerated code:")
    print("-" * 80)
    print(result["code"])
    print("-" * 80)
    
    # Optionally save the generated code
    from .save_scene import save_generated_scene
    file_path = save_generated_scene(result["class_name"], result["code"])
    print(f"\nSaved to: {file_path}") 