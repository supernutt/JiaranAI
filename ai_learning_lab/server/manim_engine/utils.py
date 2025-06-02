from pathlib import Path

def list_available_scenes():
    """
    List all available Manim scenes in the scenes directory.
    
    Returns:
        List of scene names (file stems) that can be used with AnimationGenerator
    """
    scenes_dir = Path(__file__).parent / "scenes"
    return [
        f.stem for f in scenes_dir.glob("*.py")
        if not f.name.startswith("__")
    ]

def is_valid_scene(scene_name):
    """
    Check if a scene name is valid (exists in the scenes directory).
    
    Args:
        scene_name: The name of the scene to check
        
    Returns:
        bool: True if the scene exists, False otherwise
    """
    scenes_dir = Path(__file__).parent / "scenes"
    scene_file = scenes_dir / f"{scene_name}.py"
    return scene_file.exists() 