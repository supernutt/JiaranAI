# ai-learning-lab/server/manim_engine/prompt_adapter.py

import os
import logging
from typing import Optional

from dotenv import load_dotenv, find_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file (searches parent directories)
load_dotenv(find_dotenv())

ADAPTER_SYSTEM_PROMPT = """
You are an expert educational assistant and visual explainer. Your task is to take a student's question or a concept they want to understand, and convert it into a detailed set of visual instructions for a Manim animation.
These instructions should describe *what* to draw and animate, step-by-step, to best explain the concept or answer the question.
Focus on clear visual storytelling. For example, if a student asks about \"compound interest,\" your instructions should describe animating an initial principal amount, showing growth over discrete periods, visually comparing it to simple interest, and labeling key components and totals at each step.
If a student asks, \"What's the difference between sine and cosine?\", you might instruct to: \"Plot both sine and cosine waves on the same coordinate plane. Highlight their starting points (sine at origin, cosine at 1 on y-axis). Show that the cosine wave is a phase-shifted version of the sine wave, perhaps by animating a horizontal shift of pi/2. Label key points like peaks, troughs, and zero-crossings for both.\"

Do NOT generate any Python code or Manim-specific syntax. Only return the textual description of the animation steps as a single, coherent paragraph or a short list of key actions.
If the student's request is too vague, too broad, or unclear to create specific animation instructions, provide a generic instruction like: \"Create a Manim animation that visually explains the core idea of [student's topic/question] using clear diagrams, highlighting key terms with text labels, and employing simple, illustrative animations to clarify the concept.\" (Replace [student's topic/question] with the actual topic if discernible, otherwise use 'the requested concept').

Your output should be a single string ready to be passed to another AI that will generate Manim code.
Be concise yet descriptive enough for the next AI to understand the visual narrative required.
"""

# Attempt to import OpenAI client, with graceful fallback for environments where it might not be immediately available
# although it's a core dependency for this function to actually work.
_openai_client = None
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        logger.warning("OpenAI API key not found. Prompt adapter will not function correctly without it.")
except ImportError:
    logger.warning("OpenAI SDK not found. Prompt adapter will not function correctly without it.")

def translate_user_request_to_manim_prompt(user_input: str, model_name: str = "gpt-3.5-turbo") -> str:
    """
    Translates a student's natural language question or concept request into a 
    structured Manim animation prompt (descriptive text, not code).

    Args:
        user_input: The student's question or concept request.
        model_name: The OpenAI model to use for translation (e.g., "gpt-3.5-turbo", "gpt-4").

    Returns:
        A string containing detailed drawing instructions for Manim, or a generic fallback.
    """
    if not _openai_client:
        logger.error("OpenAI client not initialized. Cannot translate user request. Ensure API key and SDK are available.")
        # Fallback if OpenAI client isn't available
        topic = user_input[:50] + "..." if len(user_input) > 50 else user_input
        return f"Create a Manim animation that visually explains the core idea of '{topic}' using clear diagrams, highlighting key terms with text labels, and employing simple, illustrative animations to clarify the concept."

    if not user_input or len(user_input.strip()) < 5: # Basic check for very short/empty input
        logger.warning(f"User input '{user_input}' is too short or empty. Returning generic prompt.")
        return "Create a Manim animation that visually explains the requested concept using clear diagrams, highlighting key terms with text labels, and employing simple, illustrative animations."

    try:
        logger.info(f"Translating user request: '{user_input[:100]}...'")
        response = _openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": ADAPTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            max_tokens=500, # Sufficient for a detailed textual prompt
            temperature=0.5  # Lower temperature for more focused, less "creative" instruction sets
        )
        
        translated_prompt = response.choices[0].message.content.strip()
        
        # Further check if the response is too generic or a refusal, which might indicate the input was too vague for the LLM.
        # This is a simple heuristic; more sophisticated checks could be added.
        if len(translated_prompt) < 50 or "sorry" in translated_prompt.lower() or "unable to" in translated_prompt.lower():
            logger.warning(f"Translated prompt seems too short or like a refusal: '{translated_prompt}'. Falling back to generic for input: '{user_input}'.")
            topic = user_input[:50] + "..." if len(user_input) > 50 else user_input
            # Extract topic more intelligently if possible, or use the refined generic from system prompt
            if "[student's topic/question]" in ADAPTER_SYSTEM_PROMPT.split("generic instruction like: ")[-1]: # a bit fragile
                 return ADAPTER_SYSTEM_PROMPT.split("generic instruction like: \"")[-1].split("\"")[0].replace("[student's topic/question]", topic)
            return f"Create a Manim animation that visually explains the core idea of '{topic}' using clear diagrams, highlighting key terms with text labels, and employing simple, illustrative animations to clarify the concept."
        
        logger.info(f"Successfully translated user request to Manim prompt: '{translated_prompt[:100]}...'")
        return translated_prompt

    except Exception as e:
        logger.error(f"Error during OpenAI call in prompt adapter: {e}")
        # Fallback in case of API error
        topic = user_input[:50] + "..." if len(user_input) > 50 else user_input
        return f"Create a Manim animation that visually explains the core idea of '{topic}' using clear diagrams, highlighting key terms with text labels, and employing simple, illustrative animations to clarify the concept."

if __name__ == '__main__':
    # Simple test cases
    test_questions = [
        "What's the difference between sine and cosine?",
        "I don't understand the unit circle.",
        "Can you show matrix multiplication?",
        "Explain Pythagoras theorem visually.",
        "How does a basic electric circuit work?",
        "Sort an array using bubble sort, show the steps.",
        "What is DNA?", # Potentially vague
        "Tell me about black holes." # Potentially very broad
    ]

    # Ensure OPENAI_API_KEY is loaded for this test block if not already
    if not _openai_client and os.getenv("OPENAI_API_KEY"):
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    if not _openai_client:
        print("OpenAI client not available. Cannot run __main__ tests for prompt_adapter.")
        print("Please ensure OPENAI_API_KEY is set in your .env file and python-dotenv is installed.")
    else:
        for i, question in enumerate(test_questions):
            print(f"\n--- Test Case {i+1} ---")
            print(f"Student Question: {question}")
            manim_instruction_prompt = translate_user_request_to_manim_prompt(question)
            print(f"Adapted Manim Prompt: {manim_instruction_prompt}") 