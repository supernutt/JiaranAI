from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
import os
from dotenv import load_dotenv
import openai
from openai import OpenAI
import io
import json
import difflib
import re
import math # Add math import for math.exp
import PyPDF2 # Add for PDF processing

# --- Manim Engine Imports ---
from pathlib import Path
import sys

# Add manim_engine to sys.path to allow imports
# Assuming main.py is in server/ and manim_engine is in server/manim_engine/
MANIM_ENGINE_DIR = Path(__file__).parent / "manim_engine"
if str(MANIM_ENGINE_DIR) not in sys.path:
    sys.path.append(str(MANIM_ENGINE_DIR))

try:
    from animation_generator import AnimationGenerator
    from utils import is_valid_scene
    MANIM_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    MANIM_IMPORTS_SUCCESSFUL = False
    print(f"CRITICAL (server/main.py): Failed to import from manim_engine: {e}. Manim features will not work.")
    # Define dummy classes/functions if import fails, so the server can still start (optional)
    class AnimationGenerator:
        def __init__(self, *args, **kwargs): pass
        def render_scene(self, *args, **kwargs): return None
    def is_valid_scene(*args, **kwargs): return False

# --- Configuration ---
# ENSURE This points to the ROOT-LEVEL concepts.json
CONCEPTS_FILE_PATH = "../concepts.json"
FUZZY_MATCH_CUTOFF = 0.7
MAX_CONCEPTS_TO_EXTRACT = 5
MAX_QUESTIONS_TO_RETURN = 5
DEFAULT_NEW_CONCEPT_DIFFICULTY = 0.5

# Load environment variables
load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("CRITICAL (server/main.py): OPENAI_API_KEY not found. LLM features will rely on mock data or fail.")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Restrict to known origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Be explicit about allowed methods
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # Be explicit about allowed headers
    expose_headers=["Content-Disposition"],  # Headers that can be exposed to the browser
    max_age=600,  # Cache preflight requests for 10 minutes
)

# --- Manim Engine API Integration ---
# Ensure this import is after 'app = FastAPI()' and other necessary initializations
# if it depends on them, though typically router definition is self-contained.

# Add manim_engine to sys.path if not already done (it should be near the top of the file)
# MANIM_ENGINE_DIR = Path(__file__).parent / "manim_engine"
# if str(MANIM_ENGINE_DIR) not in sys.path:
# sys.path.append(str(MANIM_ENGINE_DIR))
# ^^^ This block should already be present near the top for other Manim imports.

from fastapi.staticfiles import StaticFiles # Make sure StaticFiles is imported

# Attempt to import the router from the manim_engine package
try:
    from manim_engine.api_integration import router as manim_router
    
    # Initialize the task store before mounting the router
    try:
        from manim_engine.api_integration import load_tasks_from_file
        load_tasks_from_file()
        print("Successfully loaded Manim task store.")
    except Exception as task_store_error:
        print(f"Warning: Failed to initialize Manim task store: {task_store_error}")

    app.include_router(manim_router)
    print("Successfully included Manim router.")

    # Static file serving for Manim videos
    # MANIM_ENGINE_DIR is already defined at the top of this file
    MANIM_VIDEOS_SERVE_DIR = MANIM_ENGINE_DIR / "output"
    
    # Create directory if it doesn't exist to prevent startup error for StaticFiles
    os.makedirs(MANIM_VIDEOS_SERVE_DIR, exist_ok=True)
    
    # Mount at /manim_engine_output as suggested by comments, or /animations/video as per api_integration.py example
    # Let's use /manim_engine_output to avoid conflict with /animations router prefix if videos are nested there
    # The video_url construction in api_integration.py's generate_and_render_scene_task was:
    # video_url = f"/animations/video/{video_path_for_url.as_posix()}"
    # This implies the StaticFiles mount should be at "/animations/video" to match.
    
    # Let's align with the video_url construction in api_integration.py
    # Serve files from manim_engine/output/ under /animations/video/
    # e.g., manim_engine/output/videos/SceneName/480p15/video.mp4 
    # will be accessible at http://localhost:8000/animations/video/videos/SceneName/480p15/video.mp4
    app.mount("/animations/video", StaticFiles(directory=MANIM_VIDEOS_SERVE_DIR), name="manim_videos")
    print(f"Static files for Manim videos mounted from {MANIM_VIDEOS_SERVE_DIR} at /animations/video.")

except ImportError as e:
    print(f"CRITICAL (server/main.py): Failed to import or include manim_router: {e}. Manim API endpoints will not be available.")
except Exception as e:
    print(f"CRITICAL (server/main.py): Error setting up Manim engine: {e}. Manim API endpoints may not work correctly.")
# --- End Manim Engine API Integration ---

# --- CONCEPTS_DB Handling ---
def load_concepts_db() -> Dict:
    try:
        # Correctly resolve path if this script is run from ai-learning-lab/server/
        # or if CONCEPTS_FILE_PATH is already absolute/correctly relative from execution context.
        # For simplicity, we assume CONCEPTS_FILE_PATH works as is.
        if os.path.exists(CONCEPTS_FILE_PATH):
            with open(CONCEPTS_FILE_PATH, 'r') as f:
                content = f.read()
                if not content.strip(): return {}
                return json.loads(content)
        else:
            print(f"Warning (server/main.py): '{CONCEPTS_FILE_PATH}' not found. Creating an empty one.")
            save_concepts_db({}) 
            return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading '{CONCEPTS_FILE_PATH}' in server/main.py: {e}. Returning empty DB.")
        return {}

def save_concepts_db(concepts_db: Dict):
    try:
        with open(CONCEPTS_FILE_PATH, 'w') as f:
            json.dump(concepts_db, f, indent=4)
        print(f"CONCEPTS_DB successfully saved to '{CONCEPTS_FILE_PATH}' from server/main.py.")
    except IOError as e:
        print(f"Error saving CONCEPTS_DB from server/main.py: {e}")

def slugify(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text) 
    text = re.sub(r'[\s_-]+', '_', text).strip('_')
    if not text: return "untitled_concept"
    return text
# --- End CONCEPTS_DB Handling ---

# --- Manim Test Render Helper ---
async def trigger_manim_render(scene_name: str, quality: str = "low"):
    if not MANIM_IMPORTS_SUCCESSFUL:
        return {"error": "Manim engine components not loaded. Check server logs."}

    # Determine paths relative to this main.py file
    server_root = Path(__file__).parent
    manim_engine_path = server_root / "manim_engine"
    scenes_dir = manim_engine_path / "scenes"
    output_dir = manim_engine_path / "output"

    # Ensure output directory exists (AnimationGenerator might do this, but good to be sure)
    (output_dir / "videos").mkdir(parents=True, exist_ok=True) # videos subdir is created by manim

    try:
        # Pass only the quality to the constructor
        # The AnimationGenerator will set its own scenes_dir and output_dir
        animator = AnimationGenerator(quality=quality)

        # We still need to use the scenes_dir for is_valid_scene, 
        # but it should be the one AnimationGenerator itself uses.
        # For consistency, let's use the path derived in this function, 
        # assuming AnimationGenerator correctly uses its relative paths.
        # OR, ideally, is_valid_scene should also perhaps take an AnimationGenerator instance
        # or know where to find scenes globally if not provided a path.
        # For now, let's assume the scenes_dir path used here is correct for validation.
        # Corrected call: is_valid_scene only takes scene_name
        if not is_valid_scene(scene_name):
            return {"error": f"Scene '{scene_name}' not found or invalid."}

        # render_scene was a conceptual name, the actual method is generate_animation
        # It takes scene_name and an optional file_name for the output stem.
        # Let's use the scene_name as the file_name stem for simplicity.
        output_filename_stem = scene_name # Or generate a more unique one if needed
        video_path = animator.generate_animation(scene_name, file_name=output_filename_stem)

        if video_path and Path(video_path).exists():
            # Make the path relative to the AnimationGenerator's output_dir for the URL
            # The video_path returned by generate_animation is absolute.
            # The AnimationGenerator's output_dir is self.output_dir
            ag_output_dir = animator.output_dir # This is manim_engine/output
            relative_video_path = Path(video_path).relative_to(ag_output_dir)
            return {
                "message": f"Successfully rendered '{scene_name}'",
                "video_path_on_server": video_path,
                "accessible_at_manim_engine_static_output": str(relative_video_path)
            }
        else:
            return {"error": f"Failed to render '{scene_name}' or video path not found."}
    except Exception as e:
        print(f"Error during Manim render for '{scene_name}': {e}")
        return {"error": f"Exception during Manim render: {str(e)}"}

# --- Pydantic Models ---
class DiagnosticRequest(BaseModel):
    content: str

class DiagnosticQuestion(BaseModel):
    concept: str
    question: str
    option_a: str
    option_b: str
    correct_answer: Literal["a", "b"]
    explanation: str
    difficulty: float = 0.5  # Added difficulty field with default value

class DiagnosticResponse(BaseModel):
    questions: List[DiagnosticQuestion]

class ClassroomRequest(BaseModel):
    topic: str

class Character(BaseModel):
    name: str
    statement: str

class ClassroomResponse(BaseModel):
    discussion: List[Character]

# --- User model constants ---
# Bayesian update parameters
P_R_CORRECT_GIVEN_C_TRUE = 0.9  # P(R=correct | C=true)
P_R_CORRECT_GIVEN_C_FALSE = 0.2 # P(R=correct | C=false)
P_R_INCORRECT_GIVEN_C_TRUE = 1 - P_R_CORRECT_GIVEN_C_TRUE # P(R=incorrect | C=true)
P_R_INCORRECT_GIVEN_C_FALSE = 1 - P_R_CORRECT_GIVEN_C_FALSE # P(R=incorrect | C=false)

INITIAL_P_MASTERY = 0.4
MAX_ATTEMPTS_THRESHOLD = 5
P_MASTERY_THRESHOLD = 0.85
IDEAL_DIFFICULTY_TARGET = 0.5

# Added constants for belief distribution
NUM_BELIEF_POINTS = 10 # Number of points in the discrete belief distribution
BELIEF_ABILITY_LEVELS = [i / NUM_BELIEF_POINTS for i in range(NUM_BELIEF_POINTS)] # [0.0, 0.1, ..., 0.9]
DEFAULT_CONCEPT_DIFFICULTY_FOR_BELIEF = 0.5 # d parameter for sigmoid

# In-memory store for user models
user_models: Dict[str, Dict[str, Dict]] = {}

class DiagnosticRequestForResponse(BaseModel):
    user_id: str
    concept: str
    response: Literal["correct", "incorrect", "unsure"]
    difficulty: float = DEFAULT_CONCEPT_DIFFICULTY_FOR_BELIEF  # Add difficulty with default

class BeliefPoint(BaseModel):
    a: float # ability level
    p: float # probability

class DiagnosticResponseForClient(BaseModel):
    concept: str
    updated_belief: List[BeliefPoint]

class ConceptState(BaseModel):
    belief: List[BeliefPoint]
    attempts: int
    correct: int

class ConceptMetadata(BaseModel):
    title: str
    description: str
    difficulty: float

# Helper function for sigmoid calculation
def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

@app.post("/upload-content", response_model=str)
async def upload_content(file: Optional[UploadFile] = File(None), text_content: Optional[str] = Form(None)):
    """
    Upload text content either as a file or as raw text.
    Returns the extracted text content.
    """
    if file:
        # Read the file content
        content = await file.read()
        
        # Handle .txt files
        if file.filename.endswith(".txt"):
            return content.decode("utf-8")
        
        # Handle .pdf files
        elif file.filename.endswith(".pdf"):
            try:
                # Create a BytesIO object from the content
                pdf_file = io.BytesIO(content)
                
                # Create a PDF reader object
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
                
                # Check if we extracted any meaningful text
                if not text.strip():
                    raise HTTPException(status_code=400, detail="Could not extract text from the PDF. The file may be scanned or encrypted.")
                
                return text
            except Exception as e:
                print(f"Error extracting text from PDF: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error processing PDF file: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Only .txt and .pdf files are supported at this time")
    elif text_content:
        return text_content
    else:
        raise HTTPException(status_code=400, detail="Either file or text_content must be provided")

@app.post("/generate-diagnostic", response_model=DiagnosticResponse)
async def generate_diagnostic(request: DiagnosticRequest):
    if not client:
        print("OpenAI client not initialized in server/main.py. Falling back to mock.")
        return _get_mock_diagnostic_response()

    uploaded_content = request.content
    concepts_db = load_concepts_db()
    concepts_db_changed = False
    generated_questions_for_response: List[DiagnosticQuestion] = []

    # 1. Revised LLM Prompt and single call for concepts, groups, and questions
    try:
        prompt = (
            f"Analyze the following content and generate up to {MAX_QUESTIONS_TO_RETURN} diagnostic questions. "
            f"For each question, identify the specific 'concept' it assesses and assign it to a broader 'group'. "
            f"Group related concepts under meaningful umbrella terms. For example, group 'delusion', 'obsession', and 'sleep disorders' under 'Mental Health Concepts'. "
            f"If a concept doesn't belong to any existing group, create a new, sensible group name based on the topic. "
            f"Ensure the 'group' name is concise and suitable as a category title. "
            f"The specific 'concept' field should name the granular topic the question is about, while the 'group' field is the broader category. "
            f"For each question, assign a 'difficulty' value between 0.1 (very easy) and 0.9 (very hard). Vary the difficulty levels across questions. "
            f"Respond with a valid JSON object with a single key 'questions_data', which is a list of objects. "
            f"Each object in the list must have the following fields: "
            f"  'concept' (specific topic, e.g., 'Derivative Power Rule'), "
            f"  'group' (umbrella term, e.g., 'Calculus Fundamentals'), "
            f"  'question' (the question text), "
            f"  'option_a' (text for option A), "
            f"  'option_b' (text for option B), "
            f"  'correct_answer' ('a' or 'b'), "
            f"  'explanation' (explanation for the correct answer), "
            f"  'difficulty' (a number between 0.1 and 0.9 representing question difficulty). "
            f"Example format for one item in the list: "
            f"{{ \"concept\": \"Obsession\", \"group\": \"Mental Health Concepts\", \"question\": \"Which of the following best describes an obsession?\", \"option_a\": \"A recurring unwanted thought\", \"option_b\": \"A positive goal you pursue regularly\", \"correct_answer\": \"a\", \"explanation\": \"An obsession is an intrusive thought that is hard to ignore.\", \"difficulty\": 0.6 }} "
            f"Content:\n---\n{uploaded_content}\n---"
        )

        llm_response = client.chat.completions.create(
            model="gpt-3.5-turbo", # or "gpt-4-turbo" if available and preferred
            messages=[
                {"role": "system", "content": "You are an expert in educational content analysis and question generation. Strictly adhere to the requested JSON format. Ensure group names are well-chosen umbrella terms."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        raw_response_data = json.loads(llm_response.choices[0].message.content)
        
        if "questions_data" not in raw_response_data or not isinstance(raw_response_data["questions_data"], list):
            print(f"Error (server/generate-diagnostic): LLM response missing 'questions_data' list or malformed. Response: {raw_response_data}")
            return _get_mock_diagnostic_response()

        llm_generated_items = raw_response_data["questions_data"]
    
    except Exception as e:
        print(f"Error (server/generate-diagnostic): LLM call or initial parsing failed: {e}.")
        return _get_mock_diagnostic_response()

    # 2. Update Response Parsing Logic
    for item_data in llm_generated_items:
        if len(generated_questions_for_response) >= MAX_QUESTIONS_TO_RETURN:
            break

        # 3. Validate Output Format
        required_fields = ["concept", "group", "question", "option_a", "option_b", "correct_answer", "explanation", "difficulty"]
        if not all(field in item_data for field in required_fields):
            print(f"Warning (server/generate-diagnostic): LLM item missing required fields. Item: {item_data}")
            continue
        
        original_concept_name = item_data["concept"] # Keep for potential logging or deeper analysis if needed
        group_name_from_llm = item_data["group"]
        
        # Validate difficulty value
        try:
            difficulty = float(item_data.get("difficulty", DEFAULT_NEW_CONCEPT_DIFFICULTY))
            # Ensure difficulty is within valid range
            if difficulty < 0.1 or difficulty > 0.9:
                print(f"Warning: Invalid difficulty value {difficulty} for question on '{original_concept_name}'. Adjusting to valid range.")
                difficulty = max(0.1, min(0.9, difficulty))
        except (ValueError, TypeError):
            print(f"Warning: Could not parse difficulty for question on '{original_concept_name}'. Using default.")
            difficulty = DEFAULT_NEW_CONCEPT_DIFFICULTY
        
        # Normalize the group name
        # .title() capitalizes the first letter of each word.
        # Replace underscores with spaces first, then title case, then strip.
        normalized_group = group_name_from_llm.replace("_", " ").strip()
        if not normalized_group: # Handle empty group name from LLM
            normalized_group = "General Concepts" 
        normalized_group = normalized_group.title()


        # Check if normalized_group exists in CONCEPTS_DB; if not, add it.
        # For CONCEPTS_DB, we use the title-cased, space-separated version as the key.
        # No slugification needed here for group names as keys.
        if normalized_group not in concepts_db:
            concepts_db[normalized_group] = {
                "title": normalized_group,
                "description": f"AI-derived group: {normalized_group}. Specific concept example: {original_concept_name}.",
                "difficulty": DEFAULT_NEW_CONCEPT_DIFFICULTY # Default difficulty for new groups
            }
            concepts_db_changed = True
            print(f"Info (server/generate-diagnostic): New group '{normalized_group}' added to CONCEPTS_DB.")

        # Ensure correct_answer is valid
        correct_answer = item_data["correct_answer"].lower()
        if correct_answer not in ["a", "b"]:
            print(f"Warning (server/generate-diagnostic): Invalid correct_answer '{item_data['correct_answer']}' for question on '{original_concept_name}'. Defaulting to 'a'.")
            correct_answer = "a"

        # Create DiagnosticQuestion object, keyed by the group name
        try:
            question_obj = DiagnosticQuestion(
                concept=normalized_group,  # Use normalized_group as the concept key for tracking
                question=item_data["question"],
                option_a=item_data["option_a"],
                option_b=item_data["option_b"],
                correct_answer=correct_answer,
                explanation=item_data["explanation"],
                difficulty=difficulty
            )
            generated_questions_for_response.append(question_obj)
        except Exception as pydantic_error:
            print(f"Error (server/generate-diagnostic): Pydantic validation failed for item: {item_data}. Error: {pydantic_error}")
            continue
            
    if concepts_db_changed:
        save_concepts_db(concepts_db)

    if generated_questions_for_response:
        print(f"Info (server/generate-diagnostic): Successfully generated {len(generated_questions_for_response)} questions.")
        return DiagnosticResponse(questions=generated_questions_for_response)
    else:
        print("Warning (server/generate-diagnostic): No questions generated after processing LLM response. Falling back to mock.")
        return _get_mock_diagnostic_response()

def _get_mock_diagnostic_response() -> DiagnosticResponse:
    # (Ensure this mock response is consistent and uses DiagnosticQuestion model)
    mock_q_list = [
        DiagnosticQuestion(concept="fallback_server_1", question="Mock Q1 from server: Is this a test?", option_a="Yes", option_b="No", correct_answer="a", explanation="This is a mock.", difficulty=0.5),
        DiagnosticQuestion(concept="fallback_server_2", question="Mock Q2 from server: What is 2*3?", option_a="6", option_b="5", correct_answer="a", explanation="It is 6.", difficulty=0.5)
        ]
    return DiagnosticResponse(questions=mock_q_list)

@app.post("/generate-classroom", response_model=ClassroomResponse)
async def generate_classroom(request: ClassroomRequest):
    """
    Takes a topic and returns a simulated AI classroom discussion.
    Three AI characters contribute to the conversation: Sophia, Leo, and Maya.
    """
    if not client:
        print("OpenAI client not initialized. Using mock for /generate-classroom.")
        # Simplified mock data for classroom if client is None
        mock_discussion = [
            {"name": "Sophia", "statement": f"Interesting topic: {request.topic}."},
            {"name": "Leo", "statement": "Indeed, but what are the implications?"},
            {"name": "Maya", "statement": "Let's explore that further."}
        ]
        return ClassroomResponse(discussion=mock_discussion)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Create a classroom discussion on the given topic with 3 AI characters:
                - Sophia: The curious one who asks insightful questions
                - Leo: The skeptical one who challenges assumptions
                - Maya: The explainer who clarifies concepts
                
                Each character should contribute one sentence to the conversation.
                Format the response as valid JSON with a 'discussion' array of objects,
                each containing 'name' and 'statement' fields.
                """},
                {"role": "user", "content": f"Generate a classroom discussion on: {request.topic}"}
            ],
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        return ClassroomResponse(discussion=result["discussion"])
    except Exception as e:
        print(f"Error calling OpenAI API for classroom: {str(e)}")
        mock_discussion = [
            {"name": "Sophia", "statement": f"I wonder how {request.topic} might change our understanding?"},
            {"name": "Leo", "statement": f"Are we sure about the current views on {request.topic}?"},
            {"name": "Maya", "statement": f"{request.topic} is a multifaceted subject worth discussing."}
        ]
        return ClassroomResponse(discussion=mock_discussion)

@app.post("/diagnostic-response", response_model=DiagnosticResponseForClient)
async def diagnostic_response(request: DiagnosticRequestForResponse):
    concepts_db = load_concepts_db() # Load current concepts
    db_changed = False

    user_id = request.user_id
    concept_input_from_request = request.concept # Raw concept name from the request
    response_type = request.response
    question_difficulty = request.difficulty  # Use question-specific difficulty

    target_concept_key: Optional[str] = None

    # 1. Check for direct key match
    if concept_input_from_request in concepts_db:
        target_concept_key = concept_input_from_request
    else:
        # 2. Try fuzzy matching if no direct match
        # Ensure keys are strings for difflib
        db_keys = [str(k) for k in concepts_db.keys()]
        matches = difflib.get_close_matches(concept_input_from_request.lower(), db_keys, n=1, cutoff=FUZZY_MATCH_CUTOFF)
        if matches:
            target_concept_key = matches[0]
            print(f"Info (diagnostic-response): Fuzzy matched input '{concept_input_from_request}' to existing key '{target_concept_key}'.")
    
    # 3. If no match found (neither direct nor fuzzy), create as a new concept
    if target_concept_key is None:
        new_concept_key = slugify(concept_input_from_request)
        if not new_concept_key: # Handle cases where slugify might return an empty string
            raise HTTPException(status_code=400, detail=f"Invalid concept name after slugification: {concept_input_from_request}")
        
        print(f"Info (diagnostic-response): Concept '{concept_input_from_request}' (key: '{new_concept_key}') is new. Adding to concepts_db.")
        concepts_db[new_concept_key] = {
            "title": concept_input_from_request.title(), # Title case the original input for title
            "description": f"User-derived concept: {concept_input_from_request}", 
            "difficulty": DEFAULT_NEW_CONCEPT_DIFFICULTY
        }
        db_changed = True
        target_concept_key = new_concept_key
    
    # Ensure target_concept_key is set (should be by now)
    if target_concept_key is None:
        # This should not be reached if logic above is correct
        raise HTTPException(status_code=500, detail="Failed to determine target concept key.")

    # Ensure user exists in user_models (this part of user_models logic is fine)
    if user_id not in user_models:
        user_models[user_id] = {}

    # Ensure concept exists for the user in user_models, initialize if not
    if target_concept_key not in user_models[user_id]:
        # Initialize with a uniform belief distribution
        initial_belief = [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS]
        user_models[user_id][target_concept_key] = {
            "belief": initial_belief,
            "attempts": 0,
            "correct": 0
        }
    
    concept_user_data = user_models[user_id][target_concept_key]
    current_belief_dist: List[Dict[str, float]] = concept_user_data["belief"] # List of {"a": val, "p": prob}

    if response_type == "unsure":
        if db_changed:
            save_concepts_db(concepts_db)
        # For "unsure", we return the current belief without updating it.
        belief_points_for_response = [BeliefPoint(a=item["a"], p=item["p"]) for item in current_belief_dist]
        return DiagnosticResponseForClient(concept=target_concept_key, updated_belief=belief_points_for_response)

    # Bayesian update logic using discrete belief distribution
    # Use question's difficulty instead of concept difficulty
    # concept_difficulty = concepts_db.get(target_concept_key, {}).get("difficulty", DEFAULT_CONCEPT_DIFFICULTY_FOR_BELIEF)

    new_unnormalized_belief: List[Dict[str, float]] = []
    total_p_after_likelihood = 0.0

    for belief_point in current_belief_dist:
        a = belief_point["a"] # current ability point
        prior_p_a = belief_point["p"] # prior probability of this ability point

        # Calculate likelihood P(Response | a, d) using question difficulty
        logit = a - question_difficulty
        p_correct_given_a_d = sigmoid(logit)
        
        likelihood = 0.0
        if response_type == "correct":
            likelihood = p_correct_given_a_d
            if belief_point == current_belief_dist[0]: # Increment correct count only once per update
                 concept_user_data["correct"] += 1
        elif response_type == "incorrect":
            likelihood = 1 - p_correct_given_a_d
        
        new_p_a_unnormalized = prior_p_a * likelihood
        new_unnormalized_belief.append({"a": a, "p": new_p_a_unnormalized})
        total_p_after_likelihood += new_p_a_unnormalized
    
    # Normalize the new belief distribution
    updated_belief_dist_for_storage: List[Dict[str, float]] = []
    updated_belief_for_response: List[BeliefPoint] = []

    if total_p_after_likelihood == 0: # Avoid division by zero; retain prior if likelihood sum is 0
        updated_belief_dist_for_storage = current_belief_dist 
        # Convert to BeliefPoint for response
        for item in current_belief_dist:
            updated_belief_for_response.append(BeliefPoint(a=item["a"], p=item["p"]))
    else:
        for belief_point in new_unnormalized_belief:
            normalized_p = belief_point["p"] / total_p_after_likelihood
            updated_belief_dist_for_storage.append({"a": belief_point["a"], "p": normalized_p})
            updated_belief_for_response.append(BeliefPoint(a=belief_point["a"], p=normalized_p))
            
    concept_user_data["belief"] = updated_belief_dist_for_storage
    concept_user_data["attempts"] += 1
    
    if db_changed:
        save_concepts_db(concepts_db)

    return DiagnosticResponseForClient(concept=target_concept_key, updated_belief=updated_belief_for_response)

@app.get("/user-profile/{user_id}", response_model=Dict[str, ConceptState])
async def get_user_profile(user_id: str):
    if user_id not in user_models:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Construct ConceptState objects for the response
    # to ensure belief is a List[BeliefPoint]
    profile_to_return: Dict[str, ConceptState] = {}
    user_profile_data = user_models.get(user_id, {})
    for concept_key, data in user_profile_data.items():
        # Assuming data["belief"] is List[Dict[str, float]] from storage
        # Provide a default empty list for belief if not present or malformed, or an initial uniform belief
        raw_belief = data.get("belief", [])
        if not isinstance(raw_belief, list) or not all(isinstance(bp, dict) and "a" in bp and "p" in bp for bp in raw_belief):
             # If belief is missing or malformed, initialize to uniform as a fallback for the profile display
             # This might happen if old data exists before belief distributions were implemented
            print(f"Warning (user-profile): Malformed or missing belief for {user_id} - {concept_key}. Defaulting to uniform.")
            belief_points = [BeliefPoint(a=level, p=1.0/NUM_BELIEF_POINTS) for level in BELIEF_ABILITY_LEVELS]
        else:
            belief_points = [BeliefPoint(a=bp["a"], p=bp["p"]) for bp in raw_belief]

        profile_to_return[concept_key] = ConceptState(
            belief=belief_points,
            attempts=data.get("attempts", 0),
            correct=data.get("correct", 0)
        )
    return profile_to_return

@app.get("/concepts", response_model=Dict[str, ConceptMetadata])
async def get_concepts():
    """Returns all concepts from the concepts.json file."""
    return load_concepts_db()

@app.get("/next-question/{user_id}", response_model=DiagnosticQuestion)
async def get_next_question(user_id: str):
    if not client: # Check if OpenAI client is initialized
        raise HTTPException(status_code=503, detail="OpenAI client not available for question generation. Please set OPENAI_API_KEY.")

    concepts_db = load_concepts_db() # Load from concepts.json
    user_data = user_models.get(user_id, {}) # User-specific mastery data
    candidate_concepts = []

    if not concepts_db:
        raise HTTPException(status_code=404, detail="No concepts available in the database. Cannot generate next question.")

    for concept_key, concept_meta_dict in concepts_db.items():
        if not isinstance(concept_meta_dict, dict):
            print(f"Warning (next-question): Concept metadata for '{concept_key}' is not a dictionary. Skipping.")
            continue
        try:
            # Extract relevant fields from the concept metadata
            concept_title = concept_meta_dict.get('title', concept_key)
            concept_description = concept_meta_dict.get('description', f"Concept: {concept_key}")
            concept_difficulty = float(concept_meta_dict.get('difficulty', DEFAULT_NEW_CONCEPT_DIFFICULTY))
        except Exception as e:
            print(f"Warning (next-question): Invalid metadata for concept '{concept_key}' in concepts.json: {e}. Skipping.")
            continue

        # Get user's progress on this concept, or default if not present
        user_concept_progress = user_data.get(concept_key, {
            "belief": [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS], # Default uniform belief
            "attempts": 0
        })
        
        # For ranking, we need a scalar summary of the belief. Expected value is a good candidate.
        current_belief: List[Dict[str, float]] = user_concept_progress.get("belief", [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS])
        expected_mastery = sum(bp["a"] * bp["p"] for bp in current_belief)

        attempts = user_concept_progress.get("attempts", 0)

        # Filter out concepts already mastered or attempted too many times
        if expected_mastery < P_MASTERY_THRESHOLD and attempts <= MAX_ATTEMPTS_THRESHOLD:
            candidate_concepts.append({
                "key": concept_key,
                "title": concept_title,
                "description": concept_description,
                "difficulty": concept_difficulty,
                "expected_mastery": expected_mastery,
                "attempts": attempts
            })

    if not candidate_concepts:
        raise HTTPException(status_code=404, detail="No suitable concepts available for this user based on current mastery and attempt criteria.")

    # Rank candidates:
    # 1. Lowest expected_mastery
    # 2. Difficulty closest to IDEAL_DIFFICULTY_TARGET
    # 3. Fewer attempts
    candidate_concepts.sort(key=lambda c: (
        c["expected_mastery"], # Primary sort: lowest expected mastery
        abs(c["difficulty"] - IDEAL_DIFFICULTY_TARGET), # Secondary sort: difficulty closest to target
        c["attempts"] # Tertiary sort: fewer attempts
    ))
    
    selected_concept_info = candidate_concepts[0]

    # Generate question using OpenAI for the selected concept
    prompt_text = f"Write 1 multiple choice diagnostic question (2 options, a or b) to assess understanding of the concept \"{selected_concept_info['title']}\": {selected_concept_info['description']}. Assign a difficulty level between 0.1 (very easy) and 0.9 (very hard). Format it in JSON as: {{ \"concept\": \"{selected_concept_info['key']}\", \"question\": \"...\", \"option_a\": \"...\", \"option_b\": \"...\", \"correct_answer\": \"a or b\", \"explanation\": \"...\", \"difficulty\": number_between_0.1_and_0.9 }}"
    
    try:
        llm_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in creating educational diagnostic questions. Ensure the output is valid JSON and strictly follows the requested format. The 'concept' field in the JSON should be the provided concept key. Include a random difficulty value between 0.1 (easiest) and 0.9 (hardest)."},
                {"role": "user", "content": prompt_text}
            ],
            response_format={"type": "json_object"}
        )
        question_data_str = llm_response.choices[0].message.content
        question_data = json.loads(question_data_str)

        # Basic validation and correction for LLM response
        if question_data.get("concept") != selected_concept_info['key']:
            print(f"Warning (next-question): LLM returned concept '{question_data.get('concept')}', expected '{selected_concept_info['key']}'. Overriding.")
            question_data["concept"] = selected_concept_info['key']
        if question_data.get("correct_answer") not in ["a", "b"]:
            print(f"Warning (next-question): LLM returned invalid correct_answer '{question_data.get('correct_answer')}'. Defaulting to 'a'.")
            question_data["correct_answer"] = "a" 
        
        # Validate and set difficulty
        try:
            difficulty = float(question_data.get("difficulty", 0.5))
            if difficulty < 0.1 or difficulty > 0.9:
                print(f"Warning (next-question): Invalid difficulty value {difficulty}. Adjusting to valid range.")
                question_data["difficulty"] = max(0.1, min(0.9, difficulty))
        except (ValueError, TypeError):
            print(f"Warning (next-question): Could not parse difficulty. Using default.")
            question_data["difficulty"] = 0.5
        
        # Ensure all fields for DiagnosticQuestion are present before creating the object
        for field_name in ["concept", "question", "option_a", "option_b", "correct_answer", "explanation", "difficulty"]:
            if field_name not in question_data:
                # Provide a default or raise an error if a critical field is missing from LLM
                print(f"Warning (next-question): LLM response missing field '{field_name}'. Setting to default/placeholder.")
                if field_name == "difficulty":
                    question_data[field_name] = 0.5
                else:
                    question_data[field_name] = f"Missing field: {field_name}" # Example placeholder

        return DiagnosticQuestion(**question_data)
    except Exception as e:
        print(f"Error (next-question): Failed to generate question via OpenAI for concept '{selected_concept_info['title']}': {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to generate question via OpenAI for concept '{selected_concept_info['title']}'. Error: {str(e)}")

@app.get("/next-question-batch/{user_id}", response_model=List[DiagnosticQuestion])
async def get_next_question_batch(user_id: str, count: int = 5):
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI client not available. Please set OPENAI_API_KEY.")
    if count <= 0 or count > 10: # Max 10 questions per batch for sanity
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10.")

    concepts_db = load_concepts_db()
    user_data = user_models.get(user_id, {})
    generated_questions: List[DiagnosticQuestion] = []
    candidate_concepts_for_ranking = []

    if not concepts_db:
        # If DB is empty, we can't generate concept-based questions.
        raise HTTPException(status_code=404, detail="No concepts available in the database to generate questions.")

    for concept_key, concept_meta_dict in concepts_db.items():
        if not isinstance(concept_meta_dict, dict):
            print(f"Warning (next-batch): Concept metadata for '{concept_key}' is not a dict. Skipping.")
            continue
        
        try:
            # Extract relevant fields from the concept metadata
            concept_title = concept_meta_dict.get('title', concept_key)
            concept_description = concept_meta_dict.get('description', f"Concept: {concept_key}")
            concept_difficulty = float(concept_meta_dict.get('difficulty', DEFAULT_NEW_CONCEPT_DIFFICULTY))
        except Exception as e:
            print(f"Warning (next-batch): Invalid metadata for '{concept_key}': {e}. Skipping.")
            continue

        user_concept_progress = user_data.get(concept_key, {
            # "p_mastery": INITIAL_P_MASTERY,
            "belief": [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS],
            "attempts": 0
        })
        
        # For ranking, we need a scalar summary of the belief. Expected value is a good candidate.
        current_belief_for_batch: List[Dict[str, float]] = user_concept_progress.get("belief", [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS])
        expected_mastery_for_batch = sum(bp["a"] * bp["p"] for bp in current_belief_for_batch)
        attempts = user_concept_progress.get("attempts", 0)

        # Filter: low mastery and not too many attempts
        if expected_mastery_for_batch < P_MASTERY_THRESHOLD and attempts <= MAX_ATTEMPTS_THRESHOLD:
            candidate_concepts_for_ranking.append({
                "key": concept_key,
                "title": concept_title,
                "description": concept_description,
                "difficulty": concept_difficulty,
                "expected_mastery": expected_mastery_for_batch,
                "attempts": attempts
            })
    
    if not candidate_concepts_for_ranking:
        raise HTTPException(status_code=404, detail="No suitable concepts for this user based on current criteria.")

    # Rank candidates:
    # 1. Lowest expected_mastery
    # 2. Difficulty closest to IDEAL_DIFFICULTY_TARGET
    # 3. Fewer attempts
    candidate_concepts_for_ranking.sort(key=lambda c: (
        c["expected_mastery"],
        abs(c["difficulty"] - IDEAL_DIFFICULTY_TARGET),
        c["attempts"]
    ))

    # Select top N concepts for the batch
    concepts_for_this_batch = candidate_concepts_for_ranking[:count]

    for selected_concept_info in concepts_for_this_batch:
        prompt_text = f"Write 1 multiple choice diagnostic question (2 options, a or b) to assess understanding of the concept \"{selected_concept_info['title']}\": {selected_concept_info['description']}. Assign a difficulty level between 0.1 (very easy) and 0.9 (very hard). Format it in JSON as: {{ \"concept\": \"{selected_concept_info['key']}\", \"question\": \"...\", \"option_a\": \"...\", \"option_b\": \"...\", \"correct_answer\": \"a or b\", \"explanation\": \"...\", \"difficulty\": number_between_0.1_and_0.9 }}"
        try:
            llm_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert creating educational diagnostic questions. Ensure valid JSON output with the specified 'concept' key. Include a random difficulty value between 0.1 (easiest) and 0.9 (hardest)."},
                    {"role": "user", "content": prompt_text}
                ],
                response_format={"type": "json_object"}
            )
            question_data_str = llm_response.choices[0].message.content
            question_data = json.loads(question_data_str)

            if question_data.get("concept") != selected_concept_info['key']:
                question_data["concept"] = selected_concept_info['key']
            if question_data.get("correct_answer") not in ["a", "b"]:
                question_data["correct_answer"] = "a"
            
            # Validate and set difficulty
            try:
                difficulty = float(question_data.get("difficulty", 0.5))
                if difficulty < 0.1 or difficulty > 0.9:
                    print(f"Warning (next-batch): Invalid difficulty value {difficulty}. Adjusting to valid range.")
                    question_data["difficulty"] = max(0.1, min(0.9, difficulty))
            except (ValueError, TypeError):
                print(f"Warning (next-batch): Could not parse difficulty. Using default.")
                question_data["difficulty"] = 0.5
            
            for field_name in ["concept", "question", "option_a", "option_b", "correct_answer", "explanation", "difficulty"]:
                if field_name not in question_data:
                    if field_name == "difficulty":
                        question_data[field_name] = 0.5
                    else:
                        question_data[field_name] = f"Missing field: {field_name}"
            
            generated_questions.append(DiagnosticQuestion(**question_data))
        except Exception as e:
            print(f"Error (next-batch): OpenAI call failed for concept '{selected_concept_info['title']}': {str(e)}. Skipping this question for the batch.")
    
    if not generated_questions:
        # If after trying all selected concepts, no questions were generated (e.g., all LLM calls failed)
        raise HTTPException(status_code=503, detail="Failed to generate any questions for the selected concepts in the batch.")

    return generated_questions

# --- Health Check & Manim Test ---
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "manim_imports_successful": MANIM_IMPORTS_SUCCESSFUL}

@app.get("/test-manim-render")
async def test_manim_render_route():
    return await trigger_manim_render("WriteHello")

# --- Potentially add uvicorn startup if this file is run directly ---
# if __name__ == "__main__":
#     import uvicorn
#     # Note: manim_engine.api_integration also runs on 8008 by default.
#     # Change port if running both simultaneously from the same machine.
#     uvicorn.run(app, host="0.0.0.0", port=8000)
