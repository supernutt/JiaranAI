# ai-learning-lab/server/manim_engine/save_scene.py

import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Basic blacklist for potentially dangerous code in LLM output
# This is a very basic security measure. For production, consider proper sandboxing.
DANGEROUS_KEYWORDS = [
    "subprocess", "os.system", "eval", "exec", "open", # open is okay if only for reading scene assets, but risky
    "socket", "urllib", "requests", "shutil", "ctypes", "multiprocessing", "pickle", "shelve"
]

PYTHON_FILE_OPERATION_KEYWORDS = ["open("]

# Modules that Manim scenes are generally allowed to import
MANIM_ALLOWED_IMPORTS = ["manim", "numpy", "math", "scipy", "colour"]

def extract_class_name(code: str) -> str:
    """
    Extracts the main Scene class name from Manim code.
    
    Args:
        code: The Manim Python code
        
    Returns:
        The name of the Scene class or None if not found
    """
    pattern = r"class\s+([A-Za-z0-9_]+)\s*\(\s*(?:Scene|MovingCameraScene)\s*\)"
    match = re.search(pattern, code)
    
    if match:
        return match.group(1)
    logger.warning("Could not extract class name from code using regex.")
    return None

def validate_manim_code(code: str) -> bool:
    """
    Performs basic validation and safety checks on the Manim scene code.
    
    Args:
        code: The Manim Python code to validate.
        
    Returns:
        True if the code passes validation, False otherwise.
    """
    import re
    
    # Blacklist of potentially dangerous import patterns
    DANGEROUS_IMPORTS = [
        'os', 'subprocess', 'sys', 'shutil', 'pathlib', 'glob',
        'pty', 'popen', 'commands', 'tempfile', 'platform',
        'sockets', 'socket', 'requests', 'urllib', 'webbrowser',
        'pickle', 'marshal', 'yaml', 'exec', 'eval', 'compile'
    ]
    
    # Check for some dangerous function names or patterns
    DANGEROUS_PATTERNS = [
        r'exec\s*\(', r'eval\s*\(', r'subprocess\.', r'os\.', 
        r'__import__\s*\(', r'open\s*\(', r'file\s*\(', r'system\s*\(',
        r'popen\s*\(', r'importlib', r'globals\s*\(', r'locals\s*\(',
        r'__\w+__',  # Double underscore attributes/methods
        r'lambda',  # Be cautious with lambdas
        r'with\s+open', r'\.read\s*\(', r'\.write\s*\(',
    ]
    
    # Allowlist of safe imports for Manim
    MANIM_ALLOWED_IMPORTS = [
        'manim', 'numpy', 'np', 'math', 'random', 'itertools',
        'collections', 'abc', 'copy', 'typing'
    ]
    
    # Extract all import statements using regex
    import_statements = re.findall(r'(?:from\s+(\w+)(?:\.\w+)*\s+import)|(?:import\s+(\w+))', code)
    
    # Flatten the tuple list and remove empty strings
    imported_modules = []
    for imp in import_statements:
        imported_modules.extend([x for x in imp if x])
    
    # Check against blacklist
    for module in imported_modules:
        if module in DANGEROUS_IMPORTS and module not in MANIM_ALLOWED_IMPORTS:
            logger.warning(f"Potentially unsafe import detected: {module}")
            return False
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            logger.warning(f"Potentially unsafe code pattern detected: {pattern}")
            return False
    
    # Check if the code contains a class inheriting from Scene
    scene_class_pattern = r'class\s+\w+\s*\(\s*(?:manim\.)?Scene\s*\)'
    if not re.search(scene_class_pattern, code, re.IGNORECASE):
        logger.warning("No Scene class found in the generated code")
        return False
    
    # Check for construct method
    construct_method_pattern = r'def\s+construct\s*\(\s*self\s*(?:,|\))' 
    if not re.search(construct_method_pattern, code, re.IGNORECASE):
        logger.warning("No construct method found in the generated code")
        return False
    
    try:
        # Try to compile the code to check for syntax errors
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError as e:
        logger.warning(f"Generated code has syntax error: {str(e)}")
        return False

def save_generated_scene(class_name: str, code: str) -> str:
    """
    Saves generated Manim code to a Python file in the scenes directory.
    
    Args:
        class_name: Name of the scene class (will be used for filename)
        code: The Manim Python code
        
    Returns:
        Path to the saved scene file
    """
    if not class_name or not class_name[0].isupper() or "_" in class_name or " " in class_name:
        logger.warning(f"Provided class_name '{class_name}' is not ideal. Attempting to extract from code.")
        extracted = extract_class_name(code)
        if extracted:
            class_name = extracted
            logger.info(f"Using extracted class name: '{class_name}'")
        else:
            # If still no good class name, create a default or raise error
            # For now, we'll try to sanitize the provided one or default
            default_name = "DefaultGeneratedScene"
            logger.warning(f"Could not extract class name. Sanitizing '{class_name}' or using default '{default_name}'.")
            class_name = ''.join(word.capitalize() for word in re.split(r'[_\s-]', str(class_name)) if word) or default_name
            if not class_name or not class_name[0].isupper(): class_name = default_name # Final fallback
            logger.info(f"Using processed class name: '{class_name}'")
    
    # Validate the code after attempting to get a good class name
    if not validate_manim_code(code):
        raise ValueError(f"Invalid or potentially unsafe Manim code for class '{class_name}'. Cannot save.")
    
    scenes_dir = Path(__file__).parent / "scenes"
    scenes_dir.mkdir(exist_ok=True) # Ensure scenes directory exists
    
    file_name = f"{class_name}.py" # Use PascalCase for filename too
    scene_file = scenes_dir / file_name
    
    # Save the code to file
    with open(scene_file, "w") as f:
        f.write(code)
    
    logger.info(f"Saved scene '{class_name}' to {scene_file}")
    return str(scene_file) 