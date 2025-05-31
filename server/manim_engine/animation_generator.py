import os
import sys
import importlib
import subprocess
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path to the manim_engine directory
MANIM_ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(MANIM_ENGINE_DIR, "output")

class AnimationGenerator:
    """Class to handle Manim animation generation."""
    
    def __init__(self, quality="low"):
        self.base_dir = Path(__file__).parent
        self.scenes_dir = self.base_dir / "scenes"
        self.output_dir = self.base_dir / "output" # This is manim_engine/output
        self.quality = quality.lower()

        # Manim quality flags and corresponding output directory names
        self.quality_settings = {
            "low": {"flag": "-pql", "dir": "480p15"},
            "medium": {"flag": "-pm", "dir": "720p30"},
            "high": {"flag": "-pqh", "dir": "1080p60"},
            # Add other qualities if needed, e.g., production: {"flag": "-qk", "dir": "2160p60"}
        }

        if self.quality not in self.quality_settings:
            raise ValueError(f"Invalid quality '{self.quality}'. Must be one of {list(self.quality_settings.keys())}")
        
        # Create base output directory if it doesn't exist (Manim will create subdirs)
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_animation(self, scene_name: str, file_name: str = "generated"):
        py_file = self.scenes_dir / f"{scene_name}.py"
        if not py_file.exists():
            raise FileNotFoundError(f"Scene script '{scene_name}.py' not found in '{self.scenes_dir}' directory.")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = f"{file_name}_{timestamp}" # Unique stem for output file
        
        current_quality_setting = self.quality_settings[self.quality]
        manim_quality_flag = current_quality_setting["flag"]
        manim_quality_dir = current_quality_setting["dir"]

        # Manim command
        # The -o flag sets the output filename *stem*. Manim handles the rest.
        command = [
            "manim",
            manim_quality_flag,
            str(py_file),
            scene_name,
            "-o", file_stem, # Manim will use this as the base for the mp4 file name
            "--media_dir", str(self.output_dir) # Root directory for Manim's media output
        ]

        try:
            print(f"[ManimEngine] Running: {' '.join(command)}")
            # It's good practice to log stdout/stderr from subprocess for debugging
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"[ManimEngine] Manim STDOUT:\n{result.stdout}")
            if result.stderr:
                 print(f"[ManimEngine] Manim STDERR:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            error_message = f"Manim render failed for scene '{scene_name}'. Command: '{' '.join(e.cmd)}'. Return code: {e.returncode}.\nStdout: {e.stdout}\nStderr: {e.stderr}"
            print(f"[ManimEngine] Error: {error_message}")
            raise RuntimeError(error_message)

        # Construct expected video path based on Manim's default output structure
        # <media_dir>/videos/<script_name_no_ext>/<quality_dir>/<scene_name_or_output_stem>.mp4
        # Here, script_name_no_ext is scene_name (since file is SceneName.py)
        # And scene_name_or_output_stem is file_stem
        video_path = self.output_dir / "videos" / scene_name / manim_quality_dir / f"{file_stem}.mp4"
        
        if not video_path.exists():
            # Fallback: Manim might sometimes just use scene_name as the file stem if -o is problematic with some versions/configs
            # This part is a bit of a guess if the primary path fails. Better logging or specific Manim version knowledge helps.
            # For now, we stick to the documented behavior with -o and --media_dir
            fallback_path = self.output_dir / "videos" / scene_name / manim_quality_dir / f"{scene_name}.mp4" # This is less likely with -o
            
            # More robust check: scan the directory for the expected timestamped file
            # This is more complex; for now, rely on the constructed path and good error message.
            print(f"[ManimEngine] Expected video path: {video_path}")
            print(f"[ManimEngine] Fallback video path (less likely): {fallback_path}")
            # List files in the expected directory for debugging
            expected_dir = self.output_dir / "videos" / scene_name / manim_quality_dir
            if expected_dir.exists():
                print(f"[ManimEngine] Contents of {expected_dir}: {list(expected_dir.iterdir())}")
            else:
                print(f"[ManimEngine] Expected directory {expected_dir} does not exist.")
            
            raise FileNotFoundError(f"Rendered video not found at expected path: {video_path}. Check Manim output and media directory structure. It's possible Manim used a different output filename or structure.")

        return str(video_path)
    
    def run_hello_world(self, file_name: str = "hello_world"):
        """
        Run the hello world example.
        
        Returns:
            Path to the generated video file
        """
        return self.generate_animation("WriteHello", file_name=file_name)


# Simple test function
def test_animation_generator():
    """Test the animation generator with the hello world example."""
    try:
        generator = AnimationGenerator(quality="low")
        video_path = generator.run_hello_world()
        print(f"Success! Video generated at: {video_path}")
        return True
    except Exception as e:
        print(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    test_animation_generator() 