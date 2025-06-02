# ai-learning-lab/server/manim_engine/api_integration.py

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from fastapi import Path as FastAPIPath
from pydantic import BaseModel
import os
import logging
from pathlib import Path
import uuid # For generating unique task IDs
from dotenv import load_dotenv, find_dotenv
import json
import filelock  # For thread-safe file operations

# Load environment variables from .env file (searches parent directories)
# This is crucial for OPENAI_API_KEY if this app runs as a separate process.
load_dotenv(find_dotenv())

# Import manim_engine modules
from .animation_generator import AnimationGenerator
from .generate_scene import generate_manim_scene
from .save_scene import save_generated_scene
from .utils import list_available_scenes, is_valid_scene
from .retry_handler import retry_generation_with_feedback, ErrorPatternTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/animations",
    tags=["animations"],
    responses={404: {"description": "Not found"}},
)

# --- Common constants and path configurations ---
# Determine the root of the manim_engine output directory for URL construction
MANIM_ENGINE_ROOT = Path(__file__).parent
MANIM_OUTPUT_DIR = MANIM_ENGINE_ROOT / "output" # This is manim_engine/output
TASK_STORE_FILE = MANIM_ENGINE_ROOT / "task_store.json" # File to store tasks
TASK_STORE_LOCK_FILE = TASK_STORE_FILE.with_suffix(".lock") # Lock file for thread safety

# Maximum number of tasks to keep in store (oldest will be removed when this is exceeded)
MAX_TASKS_IN_STORE = 50
# --- End common constants ---

# --- Task Management with File Persistence ---

# Task status constants
class TaskStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    
# Error categories for more precise error handling
class ErrorCategory:
    VALIDATION_ERROR = "VALIDATION_ERROR"  # Input/prompt validation issues
    API_ERROR = "API_ERROR"  # OpenAI/Anthropic API errors
    CODE_GENERATION_ERROR = "CODE_GENERATION_ERROR"  # LLM generated invalid code
    RENDERING_ERROR = "RENDERING_ERROR"  # Manim rendering errors
    SYSTEM_ERROR = "SYSTEM_ERROR"  # System-level errors (file I/O, etc.)
    UNKNOWN_ERROR = "UNKNOWN_ERROR"  # Fallback

# In-memory store (will be synchronized with file)
task_store: Dict[str, Dict[str, Any]] = {}

def load_tasks_from_file():
    """Load tasks from file if it exists with proper locking."""
    global task_store
    try:
        # Use file lock to ensure thread safety
        with filelock.FileLock(TASK_STORE_LOCK_FILE):
            if TASK_STORE_FILE.exists():
                with open(TASK_STORE_FILE, 'r') as f:
                    task_store = json.load(f)
                    logger.info(f"Loaded {len(task_store)} tasks from {TASK_STORE_FILE}")
            else:
                logger.info(f"Task store file {TASK_STORE_FILE} doesn't exist yet. Starting with empty task store.")
                task_store = {}
    except Exception as e:
        logger.error(f"Error loading tasks from file: {e}")
        task_store = {}

def save_task_to_file(task_id: str, task_data: Dict[str, Any]):
    """Save a single task to the task store file with proper locking."""
    global task_store
    try:
        # Use file lock to ensure thread safety
        with filelock.FileLock(TASK_STORE_LOCK_FILE):
            # First reload the task store to prevent overwriting changes from other processes
            if TASK_STORE_FILE.exists():
                with open(TASK_STORE_FILE, 'r') as f:
                    try:
                        current_store = json.load(f)
                        # Merge with in-memory store, prioritizing our new task data
                        task_store = {**current_store, **task_store}
                    except json.JSONDecodeError:
                        logger.error(f"Corrupted task store file. Backing up and starting fresh.")
                        backup_file = TASK_STORE_FILE.with_suffix(f".backup.{uuid.uuid4()}")
                        os.rename(TASK_STORE_FILE, backup_file)
                        # Continue with current in-memory store
            
            # Update in-memory store with new task data
            task_store[task_id] = task_data
            
            # Save to file
            with open(TASK_STORE_FILE, 'w') as f:
                json.dump(task_store, f, indent=2)
            logger.debug(f"Saved task {task_id} to {TASK_STORE_FILE}")
    except Exception as e:
        logger.error(f"Error saving task {task_id} to file: {e}")

def cleanup_old_tasks(max_age_hours: int = 24, max_tasks: int = None):
    """
    Remove tasks older than the specified age to prevent indefinite growth.
    If max_tasks is specified, also keeps only that many tasks (removing oldest first).
    """
    global task_store
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with filelock.FileLock(TASK_STORE_LOCK_FILE):
            # Load current state first
            if TASK_STORE_FILE.exists():
                with open(TASK_STORE_FILE, 'r') as f:
                    task_store = json.load(f)
            
            # Identify old tasks
            tasks_to_remove = []
            for task_id, task_data in task_store.items():
                # If task has a timestamp field or creation_time field
                if "creation_time" in task_data and current_time - task_data["creation_time"] > max_age_seconds:
                    tasks_to_remove.append(task_id)
            
            # Remove old tasks
            for task_id in tasks_to_remove:
                del task_store[task_id]
            
            # Limit the number of tasks if max_tasks is specified
            if max_tasks and len(task_store) > max_tasks:
                # Sort tasks by creation_time (oldest first)
                sorted_tasks = sorted(
                    task_store.items(),
                    key=lambda x: x[1].get("creation_time", 0)
                )
                # Keep only the newest max_tasks
                excess_count = len(sorted_tasks) - max_tasks
                for i in range(excess_count):
                    # Remove oldest tasks
                    task_id = sorted_tasks[i][0]
                    del task_store[task_id]
                
                logger.info(f"Removed {excess_count} oldest tasks to stay within the {max_tasks} task limit.")
            
            # Save updated store
            with open(TASK_STORE_FILE, 'w') as f:
                json.dump(task_store, f, indent=2)
            
            if tasks_to_remove:
                logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks.")
    except Exception as e:
        logger.error(f"Error during task cleanup: {e}")

# Load tasks when module is imported - CRITICAL for persistence across server restarts
logger.info("Loading tasks from persistent storage...")
load_tasks_from_file()

# Run a cleanup of old tasks on startup
cleanup_old_tasks()
# --- End Task Management ---

# Pydantic models for API requests/responses
class AnimationRequest(BaseModel): # Renamed from AnimationPrompt for clarity
    prompt: str
    scene_name: Optional[str] = None # Client can suggest a scene name
    quality: Optional[str] = "low"
    api_choice: Optional[str] = "openai" # Default to openai for full pipeline

class GenerationInitiatedResponse(BaseModel):
    message: str
    task_id: str
    status_url: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str # PENDING, PROCESSING, SUCCESS, FAILURE
    message: Optional[str] = None
    result_url: Optional[str] = None # Full URL to the video if status is SUCCESS
    scene_name: Optional[str] = None
    error_detail: Optional[str] = None
    error_category: Optional[str] = None # Added for more detailed error information
    creation_time: Optional[float] = None
    last_updated: Optional[float] = None

class SceneDetailResponse(BaseModel): # Was SceneResponse, more specific name now
    scene_name: str
    file_path_on_server: Optional[str] = None # Absolute path on server
    video_url_for_client: Optional[str] = None # Relative URL for client for static serving
    status_message: str # General status like "success" or "error details"
    # Removed direct status field, using status_message instead for this specific response type

class AvailableScenesResponse(BaseModel):
    scenes: List[str]

def generate_and_render_scene_task(
    task_id: str,
    prompt: str, 
    requested_scene_name: Optional[str],
    api_type: str,
    quality: str
):
    """
    Background task to generate and render a scene. Updates task_store.
    """
    import time
    
    # Update task status in memory and file
    task_store[task_id]["status"] = TaskStatus.PROCESSING
    task_store[task_id]["last_updated"] = time.time()
    save_task_to_file(task_id, task_store[task_id])
    
    generated_class_name = requested_scene_name # Will be updated if LLM generates a different one
    error_tracker = ErrorPatternTracker()
    
    try:
        logger.info(f"Task {task_id}: Starting background task for prompt: '{prompt[:50]}...'")
        
        # 1. Generate scene code from prompt with retry mechanism
        try:
            generation_result = generate_manim_scene(prompt, use_api=api_type)
            generated_class_name = generation_result["class_name"]
            generated_code = generation_result["code"]
            
            # Validate the generated code and retry if needed
            from .save_scene import validate_manim_code
            if not validate_manim_code(generated_code):
                logger.warning(f"Task {task_id}: Initial code validation failed, attempting retry with feedback")
                
                # Use retry mechanism to fix the code
                retry_result, retry_info = retry_generation_with_feedback(
                    original_user_prompt=prompt,
                    llm_input_prompt_that_failed=generation_result.get("llm_prompt", prompt),
                    error_message="Code validation failed: syntax or structure issues",
                    max_retries=3,
                    task_id=task_id,
                    failed_code=generated_code,
                    error_tracker=error_tracker
                )
                
                if retry_result:
                    # Extract class name from retry result
                    from .save_scene import extract_class_name
                    retry_class_name = extract_class_name(retry_result)
                    if retry_class_name:
                        generated_class_name = retry_class_name
                    generated_code = retry_result
                    logger.info(f"Task {task_id}: Retry successful, using fixed code")
                else:
                    raise ValueError(f"Failed to generate valid code after retries: {retry_info.get('last_error', 'Unknown error')}")
            
            task_store[task_id]["scene_name_generated"] = generated_class_name
            task_store[task_id]["last_updated"] = time.time()
            save_task_to_file(task_id, task_store[task_id])
            logger.info(f"Task {task_id}: Code generated for class '{generated_class_name}'.")
            
        except Exception as e:
            logger.error(f"Task {task_id}: LLM code generation failed: {str(e)}")
            task_store[task_id]["status"] = TaskStatus.FAILURE
            task_store[task_id]["error_detail"] = f"Failed to generate animation code: {str(e)}"
            task_store[task_id]["error_category"] = ErrorCategory.CODE_GENERATION_ERROR
            task_store[task_id]["message"] = "Failed during scene code generation."
            task_store[task_id]["last_updated"] = time.time()
            save_task_to_file(task_id, task_store[task_id])
            return

        # 2. Save the generated scene code to a file
        try:
            scene_file_path = save_generated_scene(generated_class_name, generated_code)
            logger.info(f"Task {task_id}: Scene '{generated_class_name}' saved to '{scene_file_path}'")
        except Exception as e:
            logger.error(f"Task {task_id}: Failed to save generated scene: {str(e)}")
            task_store[task_id]["status"] = TaskStatus.FAILURE
            task_store[task_id]["error_detail"] = f"Failed to save scene file: {str(e)}"
            task_store[task_id]["error_category"] = ErrorCategory.SYSTEM_ERROR
            task_store[task_id]["message"] = "Failed while saving the generated scene."
            task_store[task_id]["last_updated"] = time.time()
            save_task_to_file(task_id, task_store[task_id])
            return
        
        # 3. Render the scene using Manim with retry for rendering errors
        try:
            animator = AnimationGenerator(quality=quality)
            logger.info(f"Task {task_id}: Rendering scene '{generated_class_name}' with quality '{quality}'")
            video_path_abs = animator.generate_animation(scene_name=generated_class_name, file_name=f"{generated_class_name}_{task_id[:8]}")
            logger.info(f"Task {task_id}: Video for '{generated_class_name}' rendered to '{video_path_abs}'")
        except Exception as render_error:
            logger.warning(f"Task {task_id}: Initial rendering failed, attempting retry with feedback")
            
            # Use retry mechanism for rendering errors
            from .retry_handler import retry_rendering
            retry_result, retry_info = retry_rendering(
                user_prompt=prompt,
                scene_code=generated_code,
                error_message=str(render_error),
                task_id=task_id,
                max_retries=2
            )
            
            if retry_result:
                # Save the fixed code and try rendering again
                from .save_scene import extract_class_name
                retry_class_name = extract_class_name(retry_result)
                if retry_class_name:
                    generated_class_name = retry_class_name
                
                try:
                    scene_file_path = save_generated_scene(generated_class_name, retry_result)
                    animator = AnimationGenerator(quality=quality)
                    video_path_abs = animator.generate_animation(scene_name=generated_class_name, file_name=f"{generated_class_name}_{task_id[:8]}")
                    logger.info(f"Task {task_id}: Video rendered successfully after retry")
                except Exception as final_error:
                    logger.error(f"Task {task_id}: Final rendering attempt failed: {str(final_error)}")
                    task_store[task_id]["status"] = TaskStatus.FAILURE
                    task_store[task_id]["error_detail"] = f"Failed during final video rendering: {str(final_error)}"
                    task_store[task_id]["error_category"] = ErrorCategory.RENDERING_ERROR
                    task_store[task_id]["message"] = "Failed during Manim rendering process after retries."
                    task_store[task_id]["last_updated"] = time.time()
                    save_task_to_file(task_id, task_store[task_id])
                    return
            else:
                logger.error(f"Task {task_id}: Manim rendering failed even after retries: {str(render_error)}")
                task_store[task_id]["status"] = TaskStatus.FAILURE
                task_store[task_id]["error_detail"] = f"Failed during video rendering: {str(render_error)}"
                task_store[task_id]["error_category"] = ErrorCategory.RENDERING_ERROR
                task_store[task_id]["message"] = "Failed during Manim rendering process."
                task_store[task_id]["last_updated"] = time.time()
                save_task_to_file(task_id, task_store[task_id])
                return
        
        # 4. Construct relative path for URL (relative to MANIM_OUTPUT_DIR)
        # This path will be appended to the static mount point (e.g., /animations/video/)
        try:
            video_path_for_url = Path(video_path_abs).relative_to(MANIM_OUTPUT_DIR)
            # The final URL will be constructed by prefixing with the static mount point (e.g., /animations/video/)
            # So, the result_url stored should be this relative path for consistency.
            # The client will then prefix it with http://localhost:8000/animations/video/
            # No, the client should receive the full path after the domain. 
            # e.g. /animations/video/videos/SceneName/480p15/scene.mp4
            task_store[task_id]["result_url"] = f"/animations/video/{video_path_for_url.as_posix()}"
            task_store[task_id]["status"] = TaskStatus.SUCCESS
            task_store[task_id]["message"] = "Animation generated successfully."
            task_store[task_id]["last_updated"] = time.time()
            save_task_to_file(task_id, task_store[task_id])
            logger.info(f"Task {task_id}: Completed. Video available at {task_store[task_id]['result_url']}")
        except ValueError as e:
            error_msg = f"Generated video path {video_path_abs} is not within MANIM_OUTPUT_DIR {MANIM_OUTPUT_DIR}"
            logger.error(f"Task {task_id}: {error_msg}")
            task_store[task_id]["status"] = TaskStatus.FAILURE
            task_store[task_id]["error_detail"] = error_msg
            task_store[task_id]["error_category"] = ErrorCategory.SYSTEM_ERROR
            task_store[task_id]["message"] = "Error creating video URL."
            task_store[task_id]["last_updated"] = time.time()
            save_task_to_file(task_id, task_store[task_id])

    except Exception as e:
        error_detail_msg = f"Error in task {task_id} for prompt '{prompt[:50]}...': {str(e)}"
        logger.error(error_detail_msg, exc_info=True)
        task_store[task_id]["status"] = TaskStatus.FAILURE
        task_store[task_id]["error_detail"] = str(e) # Store the actual error message
        task_store[task_id]["error_category"] = ErrorCategory.UNKNOWN_ERROR
        task_store[task_id]["message"] = "An unexpected error occurred during processing."
        task_store[task_id]["last_updated"] = time.time()
        if 'generated_class_name' in locals() and generated_class_name: # if class name was determined before error
            task_store[task_id]["scene_name_generated"] = generated_class_name
        save_task_to_file(task_id, task_store[task_id])

# API endpoints
@router.get("/scenes", response_model=AvailableScenesResponse)
async def get_available_scenes():
    """List all available Manim scenes."""
    scenes = list_available_scenes()
    return {"scenes": scenes}

@router.get("/render/{scene_name}", response_model=SceneDetailResponse)
async def render_existing_scene(
    scene_name: str = FastAPIPath(..., description="Name of the scene class to render"),
    quality: str = Query("low", description="Rendering quality (low, medium, high)")
):
    """Render an existing Manim scene. This is a blocking call."""
    if not is_valid_scene(scene_name):
        raise HTTPException(status_code=404, detail=f"Scene '{scene_name}' not found")
    
    try:
        generator = AnimationGenerator(quality=quality)
        video_path_abs = generator.generate_animation(scene_name)
        
        video_url_for_client = None
        try:
            video_path_for_url = Path(video_path_abs).relative_to(MANIM_OUTPUT_DIR)
            video_url_for_client = f"/animations/video/{video_path_for_url.as_posix()}"
        except ValueError:
            logger.error(f"Generated video path {video_path_abs} is not within MANIM_OUTPUT_DIR {MANIM_OUTPUT_DIR} for scene {scene_name}")
        
        return {
            "scene_name": scene_name,
            "file_path_on_server": video_path_abs,
            "video_url_for_client": video_url_for_client,
            "status_message": "Animation rendered successfully"
        }
    except Exception as e:
        logger.error(f"Error rendering scene {scene_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=GenerationInitiatedResponse)
async def generate_scene_api(
    background_tasks: BackgroundTasks,
    request_data: AnimationRequest = Body(...)
):
    """
    Generate and render a Manim scene from a text prompt.
    This is a non-blocking endpoint that starts the generation in a background task.
    The client should poll a status endpoint or use WebSockets to get the final result.
    """
    import time
    
    # Input validation
    if not request_data.prompt or len(request_data.prompt.strip()) < 5:
        raise HTTPException(status_code=400, detail="Prompt is too short")
    
    # Security check - reject potentially malicious prompts
    prompt = request_data.prompt.lower()
    suspicious_patterns = ['rm -rf', 'system(', 'subprocess', 'exec(', '--dangerous', 'os.remove']
    for pattern in suspicious_patterns:
        if pattern in prompt:
            raise HTTPException(
                status_code=400, 
                detail="Your prompt contains potentially unsafe patterns. Please rephrase."
            )
    
    # Validate api_choice and quality from request_data
    if request_data.api_choice not in ["mock", "anthropic", "openai"]:
        raise HTTPException(status_code=400, detail=f"Invalid api_choice: {request_data.api_choice}. Must be mock, anthropic, or openai.")
    if request_data.quality not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail=f"Invalid quality: {request_data.quality}. Must be low, medium, or high.")

    task_id = str(uuid.uuid4())
    status_url = f"/animations/status/{task_id}" # Relative URL for status

    # Initialize task in store and save to file
    task_store[task_id] = {
        "status": TaskStatus.PENDING,
        "prompt": request_data.prompt,
        "message": "Task accepted and queued for processing.",
        "result_url": None,
        "error_detail": None,
        "error_category": None,
        "scene_name_generated": request_data.scene_name, # Store initially requested, will be updated
        "creation_time": time.time(),
        "last_updated": time.time(),
        "api_choice": request_data.api_choice,
        "quality": request_data.quality
    }
    save_task_to_file(task_id, task_store[task_id])
    
    # Ensure we don't store too many tasks
    cleanup_old_tasks(max_tasks=MAX_TASKS_IN_STORE)
    
    background_tasks.add_task(
        generate_and_render_scene_task,
        task_id,
        request_data.prompt,
        request_data.scene_name, # Pass the client-suggested scene name
        request_data.api_choice,
        request_data.quality
    )
    
    logger.info(f"Task {task_id} initiated for prompt '{request_data.prompt[:50]}...'. Status URL: {status_url}")
    return {
        "message": "Animation generation started. Poll status URL for updates.",
        "task_id": task_id,
        "status_url": status_url
    }

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str = FastAPIPath(..., description="ID of the task to check")):
    """Poll this endpoint to get the status of a background generation task."""
    task = task_store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task with ID '{task_id}' not found.")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task.get("status", "UNKNOWN"),
        message=task.get("message"),
        result_url=task.get("result_url"), # This will be the full path like /animations/video/...
        scene_name=task.get("scene_name_generated"),
        error_detail=task.get("error_detail"),
        error_category=task.get("error_category"),
        creation_time=task.get("creation_time"),
        last_updated=task.get("last_updated")
    )

# Example of how to use this in your main FastAPI app:
"""
# In main.py (or your FastAPI app entry point):

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

# Assuming your main.py is in ai-learning-lab/server/
# Adjust path if main.py is elsewhere
from manim_engine.api_integration import router as manim_router

app = FastAPI()

# Mount the animations API router
app.include_router(manim_router)

# Static file serving for Manim videos
# The MANIM_OUTPUT_DIR is manim_engine/output/
# This will serve files from manim_engine/output/ under /animations/video/
# e.g., manim_engine/output/videos/SceneName/480p15/video.mp4 will be at /animations/video/videos/SceneName/480p15/video.mp4

MANIM_ENGINE_DIR_FROM_MAIN = Path(__file__).parent / "manim_engine" # Path from main.py to manim_engine
MANIM_VIDEOS_SERVE_DIR = MANIM_ENGINE_DIR_FROM_MAIN / "output"

# Create directory if it doesn't exist to prevent startup error
os.makedirs(MANIM_VIDEOS_SERVE_DIR, exist_ok=True)

app.mount("/animations/video", StaticFiles(directory=MANIM_VIDEOS_SERVE_DIR), name="manim_videos")

# Example root endpoint
@app.get("/")
async def root():
    return {"message": "AI Learning Lab Server with Manim Engine"}

# To run (from ai-learning-lab/server/ directory):
# uvicorn main:app --reload
""" 