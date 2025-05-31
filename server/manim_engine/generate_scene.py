# ai-learning-lab/server/manim_engine/generate_scene.py

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Import the new prompt adapter
from .prompt_adapter import translate_user_request_to_manim_prompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Claude system prompt for Manim scene generation
MANIM_SYSTEM_PROMPT = """
You are a Python animation assistant that specializes in Manim, the mathematical animation library used by 3Blue1Brown.

You are given short animation goals or descriptions (e.g. "Animate a triangle with labels A, B, C"). Your job is to generate valid Python code using the Manim Community Library (https://docs.manim.community).

Rules:
- Always define a class that inherits from `Scene` or `MovingCameraScene`.
- The class name must be PascalCase (e.g. `DrawTriangle`).
- Always import from `manim` at the top.
- Include `construct(self)` and use `.play()`, `.add()`, `.wait()` to animate.
- IMPORTANT: Use current Manim API: `Create()` instead of deprecated `ShowCreation()`.
- IMPORTANT: Use `MathTex()` for mathematical expressions, not just `Tex()`.
- Do NOT include explanations or markdown — only return the raw Python code.

Ready? Generate valid, clean Manim code in response to animation prompts.
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
        
        # Strip markdown code fences if present
        if generated_code.startswith("```python\n"):
            generated_code = generated_code[len("```python\n"):]
        if generated_code.startswith("```\n"):
            generated_code = generated_code[len("```\n"):]
        if generated_code.endswith("\n```"):
            generated_code = generated_code[:-len("\n```")]
        
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
            model="gpt-4",
            messages=[
                {"role": "system", "content": MANIM_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        
        # Extract and return the generated code
        generated_code = response.choices[0].message.content
        
        # Strip markdown code fences if present
        if generated_code.startswith("```python\n"):
            generated_code = generated_code[len("```python\n"):]
        if generated_code.startswith("```\n"):
            generated_code = generated_code[len("```\n"):]
        if generated_code.endswith("\n```"):
            generated_code = generated_code[:-len("\n```")]
        
        return generated_code.strip()
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise

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
    import re
    # Try to get a more meaningful class name from the descriptive prompt
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
    from save_scene import extract_class_name
    
    # Extract class name from the generated code
    class_name = extract_class_name(code)
    
    # If class name couldn't be extracted, generate a default name based on the adapted_manim_prompt
    if not class_name:
        import re
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
        "adapted_manim_prompt": adapted_manim_prompt
    }

# Example usage
if __name__ == "__main__":
    student_question = "Can you show me how matrix multiplication works with a 2x2 and a 2x1 matrix?"
    # Test with OpenAI for code generation, which now uses the adapted prompt
    result = generate_manim_scene(student_question, use_api="openai") 
    
    print(f"\n--- Test for: '{student_question}' ---")
    print(f"Adapted Manim Prompt: {result['adapted_manim_prompt']}")
    print(f"Generated class: {result['class_name']}")
    print("\nGenerated code:")
    print("-" * 80)
    print(result["code"])
    print("-" * 80)
    
    # Optionally save the generated code
    from save_scene import save_generated_scene
    file_path = save_generated_scene(result["class_name"], result["code"])
    print(f"\nSaved to: {file_path}") 