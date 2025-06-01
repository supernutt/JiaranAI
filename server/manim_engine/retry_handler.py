#!/usr/bin/env python3

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import re
import traceback
from datetime import datetime
import filelock  # Add filelock import
import random
from collections import defaultdict

"""
Retry Handler Module

This module provides a robust retry mechanism for handling failures in the Manim animation generation pipeline.
It includes error categorization, logging, and intelligent retry strategies with exponential backoff.

Key Features:
- Error categorization for different types of failures
- Detailed logging of retry attempts and errors
- Exponential backoff with jitter for retry delays
- Intelligent prompt generation for retry attempts
- File locking for thread-safe logging
- Performance monitoring and metrics
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the retry configuration from environment variable or use default
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "10"))
MAX_BACKOFF_DELAY = 10  # Maximum backoff delay in seconds

# Define path for retry log
MANIM_ENGINE_DIR = Path(__file__).parent.absolute()
LOGS_DIR = MANIM_ENGINE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
RETRY_LOG_FILE = LOGS_DIR / "retry_log.jsonl"
RETRY_LOG_LOCK_FILE = RETRY_LOG_FILE.with_suffix(".lock")  # Add lock file

# Monitoring metrics
class RetryMetrics:
    """Class to track retry performance metrics."""
    
    def __init__(self):
        self.total_retries = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.error_counts = defaultdict(int)
        self.retry_delays = []
        self.recovery_attempts = 0
        self.successful_recoveries = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging."""
        return {
            "total_retries": self.total_retries,
            "successful_retries": self.successful_retries,
            "failed_retries": self.failed_retries,
            "error_counts": dict(self.error_counts),
            "avg_retry_delay": sum(self.retry_delays) / len(self.retry_delays) if self.retry_delays else 0,
            "recovery_attempts": self.recovery_attempts,
            "successful_recoveries": self.successful_recoveries,
            "success_rate": (self.successful_retries / self.total_retries * 100) if self.total_retries > 0 else 0
        }

# Global metrics instance
metrics = RetryMetrics()

def log_metrics():
    """Log current metrics to a file."""
    metrics_file = LOGS_DIR / "retry_metrics.json"
    try:
        with open(metrics_file, "w") as f:
            json.dump(metrics.to_dict(), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write metrics: {e}")

def update_metrics(
    success: bool,
    error_category: str,
    retry_delay: float,
    recovery_attempted: bool = False,
    recovery_successful: bool = False
):
    """
    Update retry metrics.
    
    Args:
        success: Whether the retry was successful
        error_category: Category of the error
        retry_delay: Time waited before retry
        recovery_attempted: Whether system recovery was attempted
        recovery_successful: Whether system recovery was successful
    """
    metrics.total_retries += 1
    if success:
        metrics.successful_retries += 1
    else:
        metrics.failed_retries += 1
    
    metrics.error_counts[error_category] += 1
    metrics.retry_delays.append(retry_delay)
    
    if recovery_attempted:
        metrics.recovery_attempts += 1
        if recovery_successful:
            metrics.successful_recoveries += 1
    
    # Log metrics periodically
    if metrics.total_retries % 10 == 0:
        log_metrics()

def get_retry_statistics() -> Dict[str, Any]:
    """
    Get current retry statistics.
    
    Returns:
        Dict containing retry statistics
    """
    return metrics.to_dict()

class RetryCategory:
    """Categories of retries for better tracking and analysis"""
    CODE_GENERATION = "CODE_GENERATION"  # Failed to generate valid Manim code
    SYNTAX_ERROR = "SYNTAX_ERROR"  # Generated code has syntax errors
    RENDERING_ERROR = "RENDERING_ERROR"  # Manim failed to render the animation
    VALIDATION_ERROR = "VALIDATION_ERROR"  # Code validation failed (semantic or asset issues)
    POLYGON_INDEX_ERROR = "POLYGON_INDEX_ERROR"  # Specific error for Polygon indexing issues
    SVG_ASSET_ERROR = "SVG_ASSET_ERROR"  # Missing SVG assets
    API_ERROR = "API_ERROR"  # API-related errors (rate limits, timeouts, etc.)
    MEMORY_ERROR = "MEMORY_ERROR"  # Out of memory errors
    TIMEOUT_ERROR = "TIMEOUT_ERROR"  # Operation timed out
    PERMISSION_ERROR = "PERMISSION_ERROR"  # File permission issues
    NETWORK_ERROR = "NETWORK_ERROR"  # Network-related errors
    DIRECTION_CONSTANTS_ERROR = "DIRECTION_CONSTANTS_ERROR"  # Missing import for UP, DOWN, etc.
    VECTOR_FIELD_FUNCTION_ERROR = "VECTOR_FIELD_FUNCTION_ERROR"  # Incorrect function signature for vector fields
    GRAPH_LABEL_ERROR = "GRAPH_LABEL_ERROR"  # Incorrect usage of get_graph_label
    RECURRING_API_ERROR = "RECURRING_API_ERROR"  # Same API error occurring multiple times
    OTHER_ERROR = "OTHER_ERROR"  # Other uncategorized errors

def log_retry_attempt(
    task_id: str,
    attempt: int,
    error_message: str,
    error_category: str,
    original_user_prompt: str,
    llm_input_prompt: str,
    failed_code_output: Optional[str],
    template_name: Optional[str] = None,
    raw_template_code: Optional[str] = None,
    is_retry_successful: Optional[bool] = None
) -> None:
    """
    Log a retry attempt to a JSONL file with thread-safe file locking.
    
    Args:
        task_id: Unique identifier for the task
        attempt: Current retry attempt number
        error_message: The error message that triggered the retry
        error_category: Category of the error (from RetryCategory)
        original_user_prompt: The original, unmodified prompt from the user.
        llm_input_prompt: The prompt that was actually sent to the LLM for generation.
        failed_code_output: The problematic code generated by the LLM, if applicable.
        template_name: Name of the template used, if any.
        raw_template_code: The raw code of the template used, if any.
        is_retry_successful: Boolean indicating if the code generated *after* this logged error/attempt was successful.
    """
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "task_id": task_id,
        "attempt_number": attempt,
        "retry_category": error_category,
        "original_user_prompt": original_user_prompt,
        "llm_input_prompt": llm_input_prompt,
        "error_trace": error_message,
        "failed_code_output": failed_code_output,
        "template_used": bool(template_name),
        "template_name": template_name,
        "raw_template_code": raw_template_code,
        "retry_successful_after_this_log": is_retry_successful
    }
    
    try:
        # Use file lock to ensure thread safety
        with filelock.FileLock(RETRY_LOG_LOCK_FILE):
            with open(RETRY_LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to write to retry log: {e}")

def categorize_error(error_message: str) -> str:
    """
    Analyze an error message and categorize it for better handling.
    
    Args:
        error_message: The error message to categorize
    
    Returns:
        str: The category of the error (from RetryCategory)
    """
    error_trace_lower = error_message.lower()
    
    # Check for specific error patterns
    if "syntaxerror" in error_trace_lower or "invalid syntax" in error_trace_lower:
        return RetryCategory.SYNTAX_ERROR
    elif "polygon does not support indexing" in error_trace_lower or "cannot index polygon" in error_trace_lower:
        return RetryCategory.POLYGON_INDEX_ERROR
    elif "svg" in error_trace_lower and ("not found" in error_trace_lower or "missing" in error_trace_lower):
        return RetryCategory.SVG_ASSET_ERROR
    # Add specific detection for missing direction constants (UP, DOWN, etc.)
    elif "nameerror" in error_trace_lower and any(x in error_trace_lower for x in ["up", "down", "left", "right", "in", "out"]):
        return RetryCategory.DIRECTION_CONSTANTS_ERROR
    # Add specific detection for vector field function signature errors
    elif "missing 1 required positional argument: 'y'" in error_trace_lower and "slope_field_function" in error_trace_lower:
        return RetryCategory.VECTOR_FIELD_FUNCTION_ERROR
    # Add specific detection for get_graph_label errors
    elif "get_graph_label" in error_trace_lower and "unexpected keyword argument" in error_trace_lower:
        return RetryCategory.GRAPH_LABEL_ERROR
    elif "validation failed" in error_trace_lower or "invalid manim code" in error_trace_lower:
        return RetryCategory.VALIDATION_ERROR
    elif "manim render failed" in error_trace_lower or "command failed" in error_trace_lower or "subprocess.calledprocesserror" in error_trace_lower:
        return RetryCategory.RENDERING_ERROR
    elif "failed to generate" in error_trace_lower or "api error" in error_trace_lower:
        return RetryCategory.CODE_GENERATION
    elif any(x in error_trace_lower for x in ["rate limit", "api limit", "quota exceeded"]):
        return RetryCategory.API_ERROR
    elif "memory" in error_trace_lower and ("error" in error_trace_lower or "exhausted" in error_trace_lower):
        return RetryCategory.MEMORY_ERROR
    elif "timeout" in error_trace_lower or "timed out" in error_trace_lower:
        return RetryCategory.TIMEOUT_ERROR
    elif "permission denied" in error_trace_lower or "access denied" in error_trace_lower:
        return RetryCategory.PERMISSION_ERROR
    elif any(x in error_trace_lower for x in ["connection", "network", "dns", "socket"]):
        return RetryCategory.NETWORK_ERROR
    else:
        return RetryCategory.OTHER_ERROR

def clean_error_trace(error_trace: str) -> str:
    """
    Clean and truncate an error trace to include only relevant parts.
    
    Args:
        error_trace: The full error trace to clean
    
    Returns:
        str: The cleaned and truncated error trace
    """
    # Extract the most relevant parts of the error trace
    # This is a simplified version, you might want to be more sophisticated
    
    # Look for a Python traceback pattern and extract the most important part
    traceback_pattern = r"Traceback \(most recent call last\):(.*?)(?:\n\n|$)"
    traceback_match = re.search(traceback_pattern, error_trace, re.DOTALL)
    
    if traceback_match:
        # Extract traceback and focus on the last few lines
        traceback_text = traceback_match.group(1).strip()
        lines = traceback_text.split('\n')
        
        # If it's long, keep only the most important parts
        if len(lines) > 10:
            # Keep the first line (context) and last 5 lines (actual error)
            lines = [lines[0]] + ["..."] + lines[-5:]
        
        return "\n".join(lines)
    
    # If not a traceback, just return a truncated version
    if len(error_trace) > 500:
        return error_trace[:500] + "..."
    
    return error_trace

def create_retry_prompt_for_code_generation(
    original_user_prompt: str,
    llm_input_prompt_that_failed: str,
    error_message: str,
    error_category: str,
    failed_code: Optional[str],
    template_name: Optional[str] = None,
    raw_template_code: Optional[str] = None
) -> str:
    """
    Create a modified prompt for retrying code generation based on the error and template info.
    """
    cleaned_error = clean_error_trace(error_message)
    
    retry_system_message = f"The previous attempt to generate Manim code from the user's request failed. Error details below.\n"
    retry_system_message += f"User Request: {original_user_prompt}\n\n"
    
    if template_name and raw_template_code:
        retry_system_message += f"A template named '{template_name}' was used for the failed attempt.\n"
        retry_system_message += f"Original Template Code:\n```python\n{raw_template_code}\n```\n\n"
        retry_system_message += f"The LLM was initially asked to fill this template using this prompt:\n'''{llm_input_prompt_that_failed}'''\n\n"
    else:
        retry_system_message += f"The LLM was initially given this prompt (no template used):\n'''{llm_input_prompt_that_failed}'''\n\n"

    if failed_code:
        retry_system_message += f"Generated Code That Failed:\n```python\n{failed_code}\n```\n\n"
    
    retry_system_message += f"Error Message:\n```\n{cleaned_error}\n```\n\n"
    retry_system_message += "INSTRUCTIONS FOR REPAIR:\n"
    retry_system_message += "1. Analyze the user request, the template (if any), the failed code (if any), and the error message.\n"
    
    if template_name:
        retry_system_message += f"2. Your goal is to fix the previous attempt. If the template was not filled correctly, provide a corrected and COMPLETE version of the Manim scene code based on the template '{template_name}'. "
        retry_system_message += "Ensure all placeholders are appropriately filled and the resulting code is valid and addresses the user's request. Pay close attention to the instructions within the original template.\n"
    else:
        retry_system_message += "2. Your goal is to generate a correct and complete Manim scene based on the original user request, avoiding the previous error. "
        retry_system_message += "Ensure the generated code directly addresses the user's request and is syntactically correct Manim Python code.\n"
        
    retry_system_message += "3. Provide ONLY the complete, corrected Python code for the Manim scene. Do not include explanations before or after the code block.\n"
    
    # Add explicit instruction to avoid external dependencies, especially for SVG/asset errors or multiple retries
    retry_system_message += "4. IMPORTANT: DO NOT use any external assets, SVG files, or dependencies. Create all visuals using native Manim objects and methods (shapes, text, mathematical objects). "
    retry_system_message += "Even if the original request might suggest using external images, implement an alternative using only built-in Manim features.\n"

    # Add specific guidance based on the error category (can be expanded)
    if error_category == RetryCategory.POLYGON_INDEX_ERROR:
        retry_system_message += "Hint: Polygon objects in Manim cannot be indexed directly. Use methods like .get_vertices() to access points.\n"
    elif error_category == RetryCategory.SVG_ASSET_ERROR:
        retry_system_message += "Hint: DO NOT use SVG assets! The error was caused by missing or unavailable SVG files. Instead of using SVGs, create the visuals directly using Manim shapes, text, and mathematical objects. For example, instead of using an SVG of a plant, create a simplified plant using combinations of circles and rectangles with appropriate colors.\n"
    elif error_category == RetryCategory.SYNTAX_ERROR:
        retry_system_message += "Hint: Carefully check Python syntax, including indentation, colons, and parentheses.\n"
    elif error_category == RetryCategory.DIRECTION_CONSTANTS_ERROR:
        retry_system_message += "Hint: Direction constants like UP, DOWN, LEFT, RIGHT, IN, OUT must be imported from manim. Make sure to add 'from manim import *' at the top of your code. These constants are not automatically available without the import.\n"
    elif error_category == RetryCategory.VECTOR_FIELD_FUNCTION_ERROR:
        retry_system_message += "Hint: In Manim, vector field functions must take a SINGLE parameter (a point in space), not separate x and y parameters. Change your function definition from 'def slope_field_function(x, y):' to 'def slope_field_function(point):' and extract x and y components inside the function: 'x, y = point[0], point[1]'.\n"
        retry_system_message += "Example:\n```python\n# INCORRECT:\ndef slope_field_function(x, y):\n    return np.array([1, y - x, 0])\n\n# CORRECT:\ndef slope_field_function(point):  # Accept a single point parameter\n    x, y = point[0], point[1]  # Extract x and y components\n    return np.array([1, y - x, 0])\n```\n"
    elif error_category == RetryCategory.GRAPH_LABEL_ERROR:
        retry_system_message += "Hint: The get_graph_label method does not accept a 'text' parameter. Use the correct syntax: axes.get_graph_label(graph, label='label_text'). Do not use 'text=' parameter.\n"
        retry_system_message += "Example:\n```python\n# INCORRECT:\nlabel = axes.get_graph_label(graph, text='cos(x)')\n\n# CORRECT:\nlabel = axes.get_graph_label(graph, '\\cos(x)')\n# OR:\nlabel = MathTex('\\cos(x)').next_to(graph, UP)\n```\n"
    elif error_category == RetryCategory.RECURRING_API_ERROR:
        retry_system_message += "Hint: The same API error is occurring repeatedly. This often happens due to misunderstanding of how a specific Manim method works. Check the method's expected parameters and return values carefully.\n"
        # Add specific guidance based on the error trace
        if "get_graph_label" in error_message.lower():
            retry_system_message += "For get_graph_label errors: Do not use 'text=' parameter. The correct syntax is axes.get_graph_label(graph, 'label_text').\n"
        elif "missing 1 required positional argument" in error_message.lower():
            retry_system_message += "For function arguments errors: Check the function signature and ensure you're passing all required parameters and in the correct order.\n"
    elif error_category == RetryCategory.RENDERING_ERROR and template_name:
        retry_system_message += "Hint: The Manim code was syntactically valid but failed to render. Review the logic within the template filling. Simplify the animation or fix issues related to Manim API usage as per the template's intent.\n"
    elif error_category == RetryCategory.RENDERING_ERROR:
         retry_system_message += "Hint: The Manim code was syntactically valid but failed to render. Try simplifying the animation or fixing issues related to Manim API usage.\n"
    # Add more specific guidance for unexpected keyword argument errors
    if "unexpected keyword argument" in error_message.lower():
        # Extract the parameter name that caused the error
        import re
        param_match = re.search(r"unexpected keyword argument ['\"]?([^'\"]+)['\"]?", error_message.lower())
        param_name = param_match.group(1) if param_match else "unknown"
        
        retry_system_message += f"Hint: The error mentions an 'unexpected keyword argument' ('{param_name}'). This suggests incorrect API usage.\n"
        
        # Give specific advice based on the parameter
        if param_name == "color":
            retry_system_message += "For color parameters, don't pass them directly to methods like get_graph(). Instead, create the object first, then set the color with .set_color(COLOR):\n"
            retry_system_message += "INCORRECT: axes.get_graph(lambda x: np.sin(x), color=RED)\n"
            retry_system_message += "CORRECT: graph = axes.plot(lambda x: np.sin(x))\n         graph.set_color(RED)\n"
        elif param_name == "line_spacing":
            retry_system_message += "The 'line_spacing' parameter is not accepted directly in MathTex constructor. Instead, use standard spacing between MathTex objects or use a VGroup to arrange multiple MathTex objects with desired spacing.\n"
        elif param_name == "text":
            retry_system_message += "The 'text' parameter is not accepted by the get_graph_label method. The correct syntax is:\n"
            retry_system_message += "INCORRECT: label = axes.get_graph_label(graph, text='cos(x)')\n"
            retry_system_message += "CORRECT: label = axes.get_graph_label(graph, '\\cos(x)')\n"
        else:
            retry_system_message += f"Check the API documentation for the correct parameters. Try setting '{param_name}' after creating the object instead of passing it as a parameter.\n"

    retry_system_message += "\nPlease generate the corrected and complete Manim scene code now."
    return retry_system_message

def create_retry_prompt_for_rendering_error(
    original_user_prompt: str,
    scene_code_that_failed: str,
    error_message: str,
    error_category: str,
    template_name: Optional[str] = None,
    raw_template_code: Optional[str] = None
) -> str:
    """
    Create a modified prompt for retrying rendering based on the error.
    This assumes the code was syntactically valid but failed during Manim execution.
    """
    cleaned_error = clean_error_trace(error_message)
    
    retry_system_message = f"The previously generated Manim scene code was syntactically correct but failed during the rendering process. Error details below.\n"
    retry_system_message += f"User Request: {original_user_prompt}\n\n"

    if template_name and raw_template_code:
        retry_system_message += f"This code was generated using the '{template_name}' template.\n"
        # Optionally include raw_template_code if it's concise or a summary of its intent
        # retry_system_message += f"Original Template (summary/path): {template_name}\n\n"

    retry_system_message += f"Full Scene Code That Failed Rendering:\n```python\n{scene_code_that_failed}\n```\n\n"
    retry_system_message += f"Rendering Error Message:\n```\n{cleaned_error}\n```\n\n"
    retry_system_message += "INSTRUCTIONS FOR REPAIR:\n"
    retry_system_message += "1. Analyze the user request, the full scene code, and the rendering error message.\n"
    
    if template_name:
        retry_system_message += f"2. Your goal is to fix the rendering error in the provided scene code, keeping in mind it was based on the '{template_name}' template. "
        retry_system_message += "Common rendering errors include incorrect Manim API usage, issues with object properties, animation conflicts, or logical errors in the scene construction. Focus on correcting the part of the code that likely caused the error, while preserving the overall structure and intent from the user's request and the template.\n"
    else:
        retry_system_message += "2. Your goal is to fix the rendering error in the provided scene code. Common rendering errors include incorrect Manim API usage, issues with object properties, animation conflicts, or logical errors in the scene construction. Focus on correcting the part of the code that likely caused the error, while preserving the overall structure and intent from the user's request.\n"

    retry_system_message += "3. Provide ONLY the complete, corrected Python code for the Manim scene. Do not include explanations before or after the code block.\n"
    
    # Add explicit instruction to avoid external dependencies, especially for SVG/asset errors
    retry_system_message += "4. IMPORTANT: DO NOT use any external assets, SVG files, or dependencies. Create all visuals using native Manim objects and methods (shapes, text, mathematical objects). "
    retry_system_message += "Even if the original request might suggest using external images, implement an alternative using only built-in Manim features.\n"

    # Add specific guidance based on the error category
    if error_category == RetryCategory.POLYGON_INDEX_ERROR:
        retry_system_message += "Hint: Check for direct indexing of Polygon objects. Use .get_vertices() instead.\n"
    elif error_category == RetryCategory.SVG_ASSET_ERROR:
        retry_system_message += "Hint: DO NOT use SVG assets! The error was caused by missing or unavailable SVG files. Instead of using SVGs, create the visuals directly using Manim shapes, text, and mathematical objects. For example, instead of using an SVG of a plant, create a simplified plant using combinations of circles and rectangles with appropriate colors.\n"
    elif error_category == RetryCategory.DIRECTION_CONSTANTS_ERROR:
        retry_system_message += "Hint: Direction constants like UP, DOWN, LEFT, RIGHT, IN, OUT must be imported from manim. Make sure to add 'from manim import *' at the top of your code. These constants are not automatically available without the import.\n"
    elif error_category == RetryCategory.VECTOR_FIELD_FUNCTION_ERROR:
        retry_system_message += "Hint: In Manim, vector field functions must take a SINGLE parameter (a point in space), not separate x and y parameters. Change your function definition from 'def slope_field_function(x, y):' to 'def slope_field_function(point):' and extract x and y components inside the function: 'x, y = point[0], point[1]'.\n"
        retry_system_message += "Example:\n```python\n# INCORRECT:\ndef slope_field_function(x, y):\n    return np.array([1, y - x, 0])\n\n# CORRECT:\ndef slope_field_function(point):  # Accept a single point parameter\n    x, y = point[0], point[1]  # Extract x and y components\n    return np.array([1, y - x, 0])\n```\n"
    elif error_category == RetryCategory.GRAPH_LABEL_ERROR:
        retry_system_message += "Hint: The get_graph_label method does not accept a 'text' parameter. Use the correct syntax: axes.get_graph_label(graph, label='label_text'). Do not use 'text=' parameter.\n"
        retry_system_message += "Example:\n```python\n# INCORRECT:\nlabel = axes.get_graph_label(graph, text='cos(x)')\n\n# CORRECT:\nlabel = axes.get_graph_label(graph, '\\cos(x)')\n# OR:\nlabel = MathTex('\\cos(x)').next_to(graph, UP)\n```\n"
    elif error_category == RetryCategory.RECURRING_API_ERROR:
        retry_system_message += "Hint: The same API error is occurring repeatedly. This often happens due to misunderstanding of how a specific Manim method works. Check the method's expected parameters and return values carefully.\n"
        # Add specific guidance based on the error trace
        if "get_graph_label" in error_message.lower():
            retry_system_message += "For get_graph_label errors: Do not use 'text=' parameter. The correct syntax is axes.get_graph_label(graph, 'label_text').\n"
        elif "missing 1 required positional argument" in error_message.lower():
            retry_system_message += "For function arguments errors: Check the function signature and ensure you're passing all required parameters and in the correct order.\n"
    elif "valueerror" in error_message.lower():
        retry_system_message += "Hint: A ValueError occurred. Check numeric parameters, object configurations, or color strings.\n"
    elif "attributeerror" in error_message.lower():
        retry_system_message += "Hint: An AttributeError occurred. The code is likely calling a method or attribute that doesn't exist for a particular Manim object, or the object is not of the expected type.\n"
    # Add more specific guidance for unexpected keyword argument errors
    elif "unexpected keyword argument" in error_message.lower():
        # Extract the parameter name that caused the error
        import re
        param_match = re.search(r"unexpected keyword argument ['\"]?([^'\"]+)['\"]?", error_message.lower())
        param_name = param_match.group(1) if param_match else "unknown"
        
        retry_system_message += f"Hint: The error mentions an 'unexpected keyword argument' ('{param_name}'). This suggests incorrect API usage.\n"
        
        # Give specific advice based on the parameter
        if param_name == "color":
            retry_system_message += "For color parameters, don't pass them directly to methods like get_graph(). Instead, create the object first, then set the color with .set_color(COLOR):\n"
            retry_system_message += "INCORRECT: axes.get_graph(lambda x: np.sin(x), color=RED)\n"
            retry_system_message += "CORRECT: graph = axes.plot(lambda x: np.sin(x))\n         graph.set_color(RED)\n"
        elif param_name == "line_spacing":
            retry_system_message += "The 'line_spacing' parameter is not accepted directly in MathTex constructor. Instead, use standard spacing between MathTex objects or use a VGroup to arrange multiple MathTex objects with desired spacing.\n"
        elif param_name == "text":
            retry_system_message += "The 'text' parameter is not accepted by the get_graph_label method. The correct syntax is:\n"
            retry_system_message += "INCORRECT: label = axes.get_graph_label(graph, text='cos(x)')\n"
            retry_system_message += "CORRECT: label = axes.get_graph_label(graph, '\\cos(x)')\n"
        else:
            retry_system_message += f"Check the API documentation for the correct parameters. Try setting '{param_name}' after creating the object instead of passing it as a parameter.\n"
    
    retry_system_message += "\nPlease generate the corrected and complete Manim scene code now."
    return retry_system_message

def recover_from_system_error(error_message: str) -> bool:
    """
    Attempt to recover from system-level errors.
    
    Args:
        error_message: The error message to analyze
    
    Returns:
        bool: True if recovery was attempted, False otherwise
    """
    error_lower = error_message.lower()
    
    # Handle memory errors
    if "memory" in error_lower or "out of memory" in error_lower:
        try:
            import gc
            gc.collect()  # Force garbage collection
            return True
        except Exception as e:
            logger.error(f"Failed to recover from memory error: {e}")
            return False
    
    # Handle disk space errors
    if "disk" in error_lower or "space" in error_lower:
        try:
            # Clean up temporary files
            temp_dir = os.path.join(os.path.dirname(__file__), "temp")
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {file}: {e}")
            return True
        except Exception as e:
            logger.error(f"Failed to recover from disk space error: {e}")
            return False
    
    # Handle permission errors
    if "permission" in error_lower or "access denied" in error_lower:
        try:
            # Ensure log directory is writable
            log_dir = os.path.join(os.path.dirname(__file__), "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, mode=0o755)
            return True
        except Exception as e:
            logger.error(f"Failed to recover from permission error: {e}")
            return False
    
    return False

# Add a class to track error patterns across retries
class ErrorPatternTracker:
    """Class to track patterns of errors across retry attempts."""
    
    def __init__(self):
        self.error_history = []
        self.api_method_errors = defaultdict(int)
        self.error_categories = defaultdict(int)
        
    def add_error(self, error_message: str, error_category: str):
        """Add an error to the tracker."""
        self.error_history.append((error_message, error_category))
        self.error_categories[error_category] += 1
        
        # Extract API method names from error message
        api_methods = self._extract_api_methods(error_message)
        for method in api_methods:
            self.api_method_errors[method] += 1
    
    def _extract_api_methods(self, error_message: str) -> List[str]:
        """Extract API method names from error message."""
        import re
        # Common pattern for method names in error messages
        method_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)\('
        methods = re.findall(method_pattern, error_message)
        return methods
    
    def get_recurring_errors(self, min_occurrences: int = 2) -> Dict[str, int]:
        """Get methods that have recurring errors."""
        return {method: count for method, count in self.api_method_errors.items() 
                if count >= min_occurrences}
    
    def is_recurring_error(self, error_message: str, min_occurrences: int = 2) -> bool:
        """Check if an error is recurring."""
        api_methods = self._extract_api_methods(error_message)
        
        for method in api_methods:
            if self.api_method_errors.get(method, 0) >= min_occurrences:
                return True
        return False
    
    def get_most_common_error_category(self) -> str:
        """Get the most common error category."""
        if not self.error_categories:
            return RetryCategory.OTHER_ERROR
        
        return max(self.error_categories.items(), key=lambda x: x[1])[0]

def retry_generation_with_feedback(
    original_user_prompt: str,
    llm_input_prompt_that_failed: str,
    error_message: str,
    max_retries: int = MAX_RETRIES,
    task_id: Optional[str] = None,
    failed_code: Optional[str] = None,
    template_name: Optional[str] = None,
    raw_template_code: Optional[str] = None,
    is_rendering_error: bool = False,
    error_tracker: Optional[ErrorPatternTracker] = None
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Handle retry logic with exponential backoff and intelligent prompt modification.
    Now includes template awareness and error pattern tracking.
    
    Args:
        original_user_prompt: The original prompt from the user.
        llm_input_prompt_that_failed: The prompt that was sent to the LLM and resulted in an error.
        error_message: The error message that occurred.
        max_retries: Maximum number of retry attempts remaining for this cycle.
        task_id: Optional task ID for logging.
        failed_code: The code that was generated and failed (either syntax or rendering).
        template_name: Name of the template used in the failed attempt, if any.
        raw_template_code: The raw code of the template used, if any.
        is_rendering_error: True if the error occurred during Manim rendering, False if during code generation.
        error_tracker: Optional tracker for error patterns across retries.

    Returns:
        Tuple[Optional[str], Dict[str, Any]]: The regenerated code (or None if all retries fail),
                                            and a dictionary with retry information ('success', 'attempts').
    """
    # Import here to avoid circular imports
    # Ensure generate_scene provides the LLM functions directly or a way to access them
    # This might require refactoring how LLM functions are called if they are not easily accessible here.
    # For now, assuming direct import is possible or will be made so.
    from .generate_scene import generate_manim_scene_with_openai, generate_manim_scene_with_anthropic
    
    current_attempts = MAX_RETRIES - max_retries + 1

    # Initialize error tracker if not provided
    if error_tracker is None:
        error_tracker = ErrorPatternTracker()

    # Determine error category
    error_category = categorize_error(error_message)
    
    # Check if this is a recurring error and update category if needed
    if error_tracker.is_recurring_error(error_message, min_occurrences=2):
        # Override error category to indicate recurring issue
        error_category = RetryCategory.RECURRING_API_ERROR
    
    # Add this error to the tracker
    error_tracker.add_error(error_message, error_category)
    
    # Attempt system-level recovery for certain errors
    recovery_attempted = False
    recovery_successful = False
    if error_category in [RetryCategory.MEMORY_ERROR, RetryCategory.PERMISSION_ERROR] and not is_rendering_error:
        recovery_attempted = True
        recovery_successful = recover_from_system_error(error_message)
        if recovery_successful:
            logger.info(f"Task {task_id}: System-level recovery attempted for {error_category}. Proceeding with retry attempt {current_attempts}.")
    
    # Create appropriate retry prompt
    if is_rendering_error:
        if not failed_code:
            logger.error(f"Task {task_id}: Cannot retry rendering error without the failed code.")
            # Log this specific failure before returning
            log_retry_attempt(
                task_id=task_id,
                attempt=current_attempts,
                error_message="Cannot retry rendering: Missing failed_code.",
                error_category=RetryCategory.OTHER_ERROR, # Or a new category like RETRY_LOGIC_ERROR
                original_user_prompt=original_user_prompt,
                llm_input_prompt=llm_input_prompt_that_failed, # The prompt that *led* to the code that failed rendering
                failed_code_output=None,
                template_name=template_name,
                raw_template_code=raw_template_code,
                is_retry_successful=False
            )
            return None, {"success": False, "attempts": current_attempts, "error": "Missing failed code for rendering retry"}
            
        retry_llm_prompt = create_retry_prompt_for_rendering_error(
            original_user_prompt=original_user_prompt,
            scene_code_that_failed=failed_code,
            error_message=error_message,
            error_category=error_category,
            template_name=template_name,
            raw_template_code=raw_template_code
        )
    else: # Code generation error
        retry_llm_prompt = create_retry_prompt_for_code_generation(
            original_user_prompt=original_user_prompt,
            llm_input_prompt_that_failed=llm_input_prompt_that_failed,
            error_message=error_message,
            error_category=error_category,
            failed_code=failed_code, # This could be None if LLM returned empty/garbage before valid code structure
            template_name=template_name,
            raw_template_code=raw_template_code
        )
    
    # Log this retry attempt (before actual generation)
    # This log entry signifies: "We are about to attempt a retry due to this error state"
    log_retry_attempt(
        task_id=task_id,
        attempt=current_attempts,
        error_message=error_message, # The error that triggered this retry cycle
        error_category=error_category,
        original_user_prompt=original_user_prompt,
        llm_input_prompt=llm_input_prompt_that_failed, # The prompt that *led* to the current error state
        failed_code_output=failed_code, # The code (if any) that caused the error
        template_name=template_name, # Pass along template info if used
        raw_template_code=raw_template_code,
        is_retry_successful=None # Success is not yet known
    )
    
    # Apply exponential backoff with jitter
    # Base delay: 0.5s, 1s, 2s for attempts 1, 2, 3 (MAX_RETRIES - max_retries is 0, 1, 2 for these attempts)
    base_delay = (2 ** (current_attempts - 1)) * 0.5 
    jitter = random.uniform(0, 0.1 * base_delay)  # Add up to 10% jitter
    backoff_delay = min(base_delay + jitter, MAX_BACKOFF_DELAY)
    
    logger.info(f"Task {task_id}: Waiting {backoff_delay:.2f}s before retry attempt {current_attempts}/{MAX_RETRIES} (max_retries left: {max_retries-1}).")
    time.sleep(backoff_delay)
    
    # Attempt retry with the new prompt
    try:
        logger.info(f"Task {task_id}: Retry attempt {current_attempts}/{MAX_RETRIES}. Sending new prompt to LLM.")
        
        # Use OpenAI by default for retries as it's generally more reliable for code fixes
        # This choice could be made configurable or based on the original API used.
        regenerated_code = generate_manim_scene_with_openai(retry_llm_prompt)
        
        # Basic validation of regenerated code
        if not regenerated_code or "class " not in regenerated_code or "Scene" not in regenerated_code:
            raise ValueError("Regenerated code is empty or does not appear to be a valid Manim scene.")

        # Update metrics for a successful generation step in retry
        update_metrics(
            success=True, # This particular generation step was successful
            error_category=error_category, # Category of the *previous* error that led to this retry
            retry_delay=backoff_delay,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful
        )
        
        # Log that this specific retry generation was successful
        logger.info(f"Task {task_id}: Retry attempt {current_attempts} successful. Regenerated code obtained.")
        return regenerated_code, {"success": True, "attempts": current_attempts, "error_tracker": error_tracker}
    
    except Exception as e_retry:
        new_error_message = f"Retry attempt {current_attempts} itself failed: {str(e_retry)}"
        logger.error(f"Task {task_id}: {new_error_message}")
        
        # Update metrics for a failed generation step in retry
        update_metrics(
            success=False, # This particular generation step failed
            error_category=error_category, # Category of the *previous* error
            retry_delay=backoff_delay,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful # Recovery might have been for the previous error
        )
        
        # Log the failure of this specific retry generation attempt
        # This is a new error, on top of the one that triggered the retry cycle.
        log_retry_attempt(
            task_id=task_id,
            attempt=current_attempts, # Still part of the same numbered retry cycle
            error_message=new_error_message, # The error from *this* LLM call
            error_category=categorize_error(str(e_retry)), # Categorize the new error
            original_user_prompt=original_user_prompt,
            llm_input_prompt=retry_llm_prompt, # The prompt that was used for *this* failed attempt
            failed_code_output=None, # No code was successfully generated in this attempt
            template_name=template_name, # Pass along template info if used
            raw_template_code=raw_template_code,
            is_retry_successful=False
        )

        # Try again if more retries are allowed for this cycle
        if max_retries > 1:
            return retry_generation_with_feedback(
                original_user_prompt=original_user_prompt,
                llm_input_prompt_that_failed=llm_input_prompt_that_failed, # Original failing prompt for context
                error_message=f"{error_message}\nAdditionally, retry attempt {current_attempts} failed with: {str(e_retry)}", # Accumulate errors
                max_retries=max_retries - 1, # Decrement retries for this cycle
                task_id=task_id,
                failed_code=failed_code, # Original failed code that started this retry cycle
                template_name=template_name,
                raw_template_code=raw_template_code,
                is_rendering_error=is_rendering_error,
                error_tracker=error_tracker  # Pass error tracker to maintain history
            )
        
        # If we've exhausted retries for this cycle, return None and failure
        logger.warning(f"Task {task_id}: All {MAX_RETRIES} retry attempts for this cycle failed. Last error during retry: {str(e_retry)}")
        return None, {"success": False, "attempts": current_attempts, "error": f"All retries failed. Last error: {str(e_retry)}", "error_tracker": error_tracker} 

def retry_with_template(
    user_prompt: str,
    template_name: str,
    raw_template_code: str,
    llm_input_prompt: str,
    task_id: Optional[str] = None,
    max_retries: int = MAX_RETRIES
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Handle retry logic for template-based generation attempts.
    This is a wrapper around retry_generation_with_feedback that pre-configures it
    for template-based retry attempts.
    
    Args:
        user_prompt: The original prompt from the user.
        template_name: Name of the template used in the attempt.
        raw_template_code: The raw code of the template used.
        llm_input_prompt: The prompt that was sent to the LLM to fill the template.
        task_id: Optional task ID for logging.
        max_retries: Maximum number of retry attempts.

    Returns:
        Tuple[Optional[str], Dict[str, Any]]: The regenerated code (or None if all retries fail),
                                            and a dictionary with retry information.
    """
    # Initialize error tracker to monitor patterns across retries
    error_tracker = ErrorPatternTracker()
    
    # Set a default task ID if none provided
    if not task_id:
        task_id = f"template_retry_{int(time.time())}"
    
    logger.info(f"Task {task_id}: Template-based generation failed. Initiating retry process.")
    
    # The actual retry logic is delegated to retry_generation_with_feedback
    # We just pre-configure it with template-specific information
    return retry_generation_with_feedback(
        original_user_prompt=user_prompt,
        llm_input_prompt_that_failed=llm_input_prompt,
        error_message="Template-based generation failed.", # Placeholder; actual error message should be provided
        max_retries=max_retries,
        task_id=task_id,
        failed_code=None, # Since we don't have generated code yet
        template_name=template_name,
        raw_template_code=raw_template_code,
        is_rendering_error=False, # This is a generation error, not a rendering error
        error_tracker=error_tracker
    )

def retry_rendering(
    user_prompt: str,
    scene_code: str,
    error_message: str,
    task_id: Optional[str] = None,
    template_name: Optional[str] = None,
    raw_template_code: Optional[str] = None,
    max_retries: int = MAX_RETRIES
) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Handle retry logic for rendering failures.
    This is a wrapper around retry_generation_with_feedback that pre-configures it
    for rendering retry attempts.
    
    Args:
        user_prompt: The original prompt from the user.
        scene_code: The scene code that failed to render.
        error_message: The error message from the rendering attempt.
        task_id: Optional task ID for logging.
        template_name: Optional name of the template used, if any.
        raw_template_code: Optional raw code of the template used, if any.
        max_retries: Maximum number of retry attempts.

    Returns:
        Tuple[Optional[str], Dict[str, Any]]: The regenerated code (or None if all retries fail),
                                            and a dictionary with retry information.
    """
    # Initialize error tracker to monitor patterns across retries
    error_tracker = ErrorPatternTracker()
    
    # Set a default task ID if none provided
    if not task_id:
        task_id = f"render_retry_{int(time.time())}"
    
    logger.info(f"Task {task_id}: Rendering failed. Initiating retry process.")
    
    # The actual retry logic is delegated to retry_generation_with_feedback
    # We just pre-configure it for rendering-specific retry information
    return retry_generation_with_feedback(
        original_user_prompt=user_prompt,
        llm_input_prompt_that_failed="", # We don't have this for rendering failures
        error_message=error_message,
        max_retries=max_retries,
        task_id=task_id,
        failed_code=scene_code,
        template_name=template_name,
        raw_template_code=raw_template_code,
        is_rendering_error=True, # This is a rendering error
        error_tracker=error_tracker
    )

# Example of how to use the improved retry system
if __name__ == "__main__":
    # Example usage - shows how the system would be integrated into the main workflow
    # This won't actually run unless this file is executed directly
    
    # Sample user request
    user_prompt = "Create an animation showing the Pythagorean theorem"
    
    # Sample LLM prompt
    llm_prompt = "Generate Manim code for an animation showing the Pythagorean theorem"
    
    # Assume we have an initial error
    error_message = "TypeError: get_graph_label() got an unexpected keyword argument 'text'"
    
    # Initialize the error tracker
    error_tracker = ErrorPatternTracker()
    
    # First retry attempt
    regenerated_code, retry_info = retry_generation_with_feedback(
        original_user_prompt=user_prompt,
        llm_input_prompt_that_failed=llm_prompt,
        error_message=error_message,
        task_id="example_task",
        error_tracker=error_tracker
    )
    
    if retry_info["success"]:
        print("Retry successful!")
        # Now you would normally run the regenerated code
    else:
        # If the retry fails, we can access the error tracker to see what errors occurred
        error_tracker = retry_info.get("error_tracker")
        if error_tracker:
            recurring_errors = error_tracker.get_recurring_errors()
            most_common_category = error_tracker.get_most_common_error_category()
            
            print(f"All retries failed. Most common error category: {most_common_category}")
            print(f"Recurring API errors: {recurring_errors}")
            
            # This information could be used for more targeted fixes or user feedback 