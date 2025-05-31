#!/usr/bin/env python3
# ai-learning-lab/server/manim_engine/test_render.py

import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# --- Add parent directory to sys.path to resolve package imports ---
# This allows 'from generate_scene import ...' to work, and subsequently
# for 'generate_scene.py' to resolve '.prompt_adapter'
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent 
# (parent_dir should be '.../ai-learning-lab/server/')
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
# --- End of sys.path modification ---

# Load environment variables from .env file (searches parent directories)
# This helps in finding OPENAI_API_KEY when testing with --api openai
load_dotenv(find_dotenv())

from manim_engine.animation_generator import AnimationGenerator
from manim_engine.utils import list_available_scenes, is_valid_scene
from manim_engine.save_scene import save_generated_scene, extract_class_name
from manim_engine.generate_scene import generate_manim_scene

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default output directory relative to this script
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"
DEFAULT_SCENES_DIR = Path(__file__).parent / "scenes"

def main():
    parser = argparse.ArgumentParser(description="Test Manim scene rendering")
    # Default scene_name is now WriteHello (PascalCase)
    parser.add_argument("scene_name", nargs="?", default="WriteHello", 
                        help="Name of the scene class to render (default: WriteHello)")
    parser.add_argument("--prompt", type=str, 
                        help="Generate and render a scene from this prompt")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="low",
                        help="Rendering quality (default: low)")
    parser.add_argument("--api", choices=["mock", "anthropic", "openai"], default="mock",
                        help="API to use for generating scenes (default: mock)")
    parser.add_argument("--list", action="store_true",
                        help="List all available scenes")
    
    args = parser.parse_args()
    
    # List available scenes if requested
    if args.list:
        scenes = list_available_scenes()
        print("\nAvailable scenes:")
        for scene in scenes:
            print(f" - {scene}")
        return
    
    # Generate scene from prompt if provided
    if args.prompt:
        print(f"Generating scene from prompt: '{args.prompt}'")
        result = generate_manim_scene(args.prompt, use_api=args.api)
        
        class_name = result["class_name"]
        code = result["code"]
        
        print(f"Generated class: {class_name}")
        print("\nSaving scene...")
        
        try:
            file_path = save_generated_scene(class_name, code)
            print(f"Scene saved to: {file_path}")
            scene_name_to_render = class_name  # Use the generated class name
        except Exception as e:
            logger.error(f"Error saving generated scene: {e}")
            return
    else:
        scene_name_to_render = args.scene_name
    
    # Check if scene exists (using the potentially updated scene_name_to_render)
    if not is_valid_scene(scene_name_to_render):
        logger.error(f"Scene '{scene_name_to_render}' not found. Use --list to see available scenes.")
        return
    
    # Render the scene
    generator = AnimationGenerator(quality=args.quality)
    
    try:
        print(f"Rendering scene: {scene_name_to_render}...")
        file_name_stem = f"test_{scene_name_to_render.lower()}" # Keep test_ prefix and lowercase for output file stem
        result_path = generator.generate_animation(scene_name_to_render, file_name=file_name_stem)
        print(f"🎉 Video generated at: {result_path}")
    except Exception as e:
        logger.error(f"❌ Error generating video for scene '{scene_name_to_render}': {e}", exc_info=True)

if __name__ == "__main__":
    main() 