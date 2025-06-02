from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
import os
import json
import difflib
import re
import math
from openai import OpenAI
from .models import (
    DiagnosticRequest, DiagnosticQuestion, DiagnosticResponse,
    ClassroomRequest, ClassroomResponse,
    DiagnosticRequestForResponse, BeliefPoint, DiagnosticResponseForClient,
    ConceptState, ConceptMetadata
)
from pathlib import Path

router = APIRouter()

# Constants
CONCEPTS_FILE_PATH = str(Path(__file__).parent.parent.parent / "concepts.json")
FUZZY_MATCH_CUTOFF = 0.7
MAX_CONCEPTS_TO_EXTRACT = 5
MAX_QUESTIONS_TO_RETURN = 5
DEFAULT_NEW_CONCEPT_DIFFICULTY = 0.5

# Diagnostic engine constants
P_R_CORRECT_GIVEN_C_TRUE = 0.9
P_R_CORRECT_GIVEN_C_FALSE = 0.2
P_R_INCORRECT_GIVEN_C_TRUE = 1 - P_R_CORRECT_GIVEN_C_TRUE
P_R_INCORRECT_GIVEN_C_FALSE = 1 - P_R_CORRECT_GIVEN_C_FALSE
INITIAL_P_MASTERY = 0.4
MAX_ATTEMPTS_THRESHOLD = 5
P_MASTERY_THRESHOLD = 0.85
IDEAL_DIFFICULTY_TARGET = 0.5

# Added constants for belief distribution
NUM_BELIEF_POINTS = 10
BELIEF_ABILITY_LEVELS = [i / NUM_BELIEF_POINTS for i in range(NUM_BELIEF_POINTS)]
DEFAULT_CONCEPT_DIFFICULTY_FOR_BELIEF = 0.5

# In-memory store for user models
user_models: Dict[str, Dict[str, Dict]] = {}

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

def load_concepts_db() -> Dict:
    try:
        if os.path.exists(CONCEPTS_FILE_PATH):
            with open(CONCEPTS_FILE_PATH, 'r') as f:
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
        else:
            print(f"Warning (diagnostic engine): '{CONCEPTS_FILE_PATH}' not found. Creating an empty one.")
            save_concepts_db({})
            return {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading '{CONCEPTS_FILE_PATH}' in diagnostic engine: {e}. Returning empty DB.")
        return {}

def save_concepts_db(concepts_db: Dict):
    try:
        with open(CONCEPTS_FILE_PATH, 'w') as f:
            json.dump(concepts_db, f, indent=4)
        print(f"CONCEPTS_DB successfully saved to '{CONCEPTS_FILE_PATH}' from diagnostic engine.")
    except IOError as e:
        print(f"Error saving CONCEPTS_DB from diagnostic engine: {e}")

def slugify(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '_', text).strip('_')
    if not text:
        return "untitled_concept"
    return text

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

def _get_mock_diagnostic_response() -> DiagnosticResponse:
    mock_q_list = [
        DiagnosticQuestion(
            concept="fallback_server_1",
            question="Mock Q1 from server: Is this a test?",
            option_a="Yes",
            option_b="No",
            correct_answer="a",
            explanation="This is a mock.",
            difficulty=0.5
        ),
        DiagnosticQuestion(
            concept="fallback_server_2",
            question="Mock Q2 from server: What is 2*3?",
            option_a="6",
            option_b="5",
            correct_answer="a",
            explanation="It is 6.",
            difficulty=0.5
        )
    ]
    return DiagnosticResponse(questions=mock_q_list)

@router.post("/generate-diagnostic", response_model=DiagnosticResponse)
async def generate_diagnostic(request: DiagnosticRequest):
    if not client:
        print("OpenAI client not initialized in diagnostic engine. Falling back to mock.")
        return _get_mock_diagnostic_response()

    uploaded_content = request.content
    concepts_db = load_concepts_db()
    concepts_db_changed = False
    generated_questions_for_response: List[DiagnosticQuestion] = []

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
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in educational content analysis and question generation. Strictly adhere to the requested JSON format. Ensure group names are well-chosen umbrella terms."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        raw_response_data = json.loads(llm_response.choices[0].message.content)
        
        if "questions_data" not in raw_response_data or not isinstance(raw_response_data["questions_data"], list):
            print(f"Error (diagnostic/generate-diagnostic): LLM response missing 'questions_data' list or malformed. Response: {raw_response_data}")
            return _get_mock_diagnostic_response()

        llm_generated_items = raw_response_data["questions_data"]
    
    except Exception as e:
        print(f"Error (diagnostic/generate-diagnostic): LLM call or initial parsing failed: {e}.")
        return _get_mock_diagnostic_response()

    for item_data in llm_generated_items:
        if len(generated_questions_for_response) >= MAX_QUESTIONS_TO_RETURN:
            break

        required_fields = ["concept", "group", "question", "option_a", "option_b", "correct_answer", "explanation", "difficulty"]
        if not all(field in item_data for field in required_fields):
            print(f"Warning (diagnostic/generate-diagnostic): LLM item missing required fields. Item: {item_data}")
            continue
        
        original_concept_name = item_data["concept"]
        group_name_from_llm = item_data["group"]
        
        try:
            difficulty = float(item_data.get("difficulty", DEFAULT_NEW_CONCEPT_DIFFICULTY))
            if difficulty < 0.1 or difficulty > 0.9:
                print(f"Warning: Invalid difficulty value {difficulty} for question on '{original_concept_name}'. Adjusting to valid range.")
                difficulty = max(0.1, min(0.9, difficulty))
        except (ValueError, TypeError):
            print(f"Warning: Could not parse difficulty for question on '{original_concept_name}'. Using default.")
            difficulty = DEFAULT_NEW_CONCEPT_DIFFICULTY
        
        normalized_group = group_name_from_llm.replace("_", " ").strip()
        if not normalized_group:
            normalized_group = "General Concepts"
        normalized_group = normalized_group.title()

        if normalized_group not in concepts_db:
            concepts_db[normalized_group] = {
                "title": normalized_group,
                "description": f"AI-derived group: {normalized_group}. Specific concept example: {original_concept_name}.",
                "difficulty": DEFAULT_NEW_CONCEPT_DIFFICULTY
            }
            concepts_db_changed = True
            print(f"Info (diagnostic/generate-diagnostic): New group '{normalized_group}' added to CONCEPTS_DB.")

        correct_answer = item_data["correct_answer"].lower()
        if correct_answer not in ["a", "b"]:
            print(f"Warning (diagnostic/generate-diagnostic): Invalid correct_answer '{item_data['correct_answer']}' for question on '{original_concept_name}'. Defaulting to 'a'.")
            correct_answer = "a"

        try:
            question_obj = DiagnosticQuestion(
                concept=normalized_group,
                question=item_data["question"],
                option_a=item_data["option_a"],
                option_b=item_data["option_b"],
                correct_answer=correct_answer,
                explanation=item_data["explanation"],
                difficulty=difficulty
            )
            generated_questions_for_response.append(question_obj)
        except Exception as pydantic_error:
            print(f"Error (diagnostic/generate-diagnostic): Pydantic validation failed for item: {item_data}. Error: {pydantic_error}")
            continue
            
    if concepts_db_changed:
        save_concepts_db(concepts_db)

    if generated_questions_for_response:
        print(f"Info (diagnostic/generate-diagnostic): Successfully generated {len(generated_questions_for_response)} questions.")
        return DiagnosticResponse(questions=generated_questions_for_response)
    else:
        print("Warning (diagnostic/generate-diagnostic): No questions generated after processing LLM response. Falling back to mock.")
        return _get_mock_diagnostic_response()

@router.post("/generate-classroom", response_model=ClassroomResponse)
async def generate_classroom(request: ClassroomRequest):
    """
    Takes a topic and returns a simulated AI classroom discussion.
    Three AI characters contribute to the conversation: Sophia, Leo, and Maya.
    """
    if not client:
        print("OpenAI client not initialized. Using mock for /generate-classroom.")
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

@router.post("/diagnostic-response", response_model=DiagnosticResponseForClient)
async def diagnostic_response(request: DiagnosticRequestForResponse):
    concepts_db = load_concepts_db()
    db_changed = False

    user_id = request.user_id
    concept_input_from_request = request.concept
    response_type = request.response
    question_difficulty = request.difficulty

    target_concept_key: Optional[str] = None

    if concept_input_from_request in concepts_db:
        target_concept_key = concept_input_from_request
    else:
        db_keys = [str(k) for k in concepts_db.keys()]
        matches = difflib.get_close_matches(concept_input_from_request.lower(), db_keys, n=1, cutoff=FUZZY_MATCH_CUTOFF)
        if matches:
            target_concept_key = matches[0]
            print(f"Info (diagnostic-response): Fuzzy matched input '{concept_input_from_request}' to existing key '{target_concept_key}'.")
    
    if target_concept_key is None:
        new_concept_key = slugify(concept_input_from_request)
        if not new_concept_key:
            raise HTTPException(status_code=400, detail=f"Invalid concept name after slugification: {concept_input_from_request}")
        
        print(f"Info (diagnostic-response): Concept '{concept_input_from_request}' (key: '{new_concept_key}') is new. Adding to concepts_db.")
        concepts_db[new_concept_key] = {
            "title": concept_input_from_request.title(),
            "description": f"User-derived concept: {concept_input_from_request}",
            "difficulty": DEFAULT_NEW_CONCEPT_DIFFICULTY
        }
        db_changed = True
        target_concept_key = new_concept_key
    
    if target_concept_key is None:
        raise HTTPException(status_code=500, detail="Failed to determine target concept key.")

    if user_id not in user_models:
        user_models[user_id] = {}

    if target_concept_key not in user_models[user_id]:
        initial_belief = [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS]
        user_models[user_id][target_concept_key] = {
            "belief": initial_belief,
            "attempts": 0,
            "correct": 0
        }
    
    concept_user_data = user_models[user_id][target_concept_key]
    current_belief_dist: List[Dict[str, float]] = concept_user_data["belief"]

    if response_type == "unsure":
        if db_changed:
            save_concepts_db(concepts_db)
        belief_points_for_response = [BeliefPoint(a=item["a"], p=item["p"]) for item in current_belief_dist]
        return DiagnosticResponseForClient(concept=target_concept_key, updated_belief=belief_points_for_response)

    new_unnormalized_belief: List[Dict[str, float]] = []
    total_p_after_likelihood = 0.0

    for belief_point in current_belief_dist:
        a = belief_point["a"]
        prior_p_a = belief_point["p"]

        logit = a - question_difficulty
        p_correct_given_a_d = sigmoid(logit)
        
        likelihood = 0.0
        if response_type == "correct":
            likelihood = p_correct_given_a_d
            if belief_point == current_belief_dist[0]:
                concept_user_data["correct"] += 1
        elif response_type == "incorrect":
            likelihood = 1 - p_correct_given_a_d
        
        new_p_a_unnormalized = prior_p_a * likelihood
        new_unnormalized_belief.append({"a": a, "p": new_p_a_unnormalized})
        total_p_after_likelihood += new_p_a_unnormalized
    
    updated_belief_dist_for_storage: List[Dict[str, float]] = []
    updated_belief_for_response: List[BeliefPoint] = []

    if total_p_after_likelihood == 0:
        updated_belief_dist_for_storage = current_belief_dist
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

@router.get("/user-profile/{user_id}", response_model=Dict[str, ConceptState])
async def get_user_profile(user_id: str):
    if user_id not in user_models:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile_to_return: Dict[str, ConceptState] = {}
    user_profile_data = user_models.get(user_id, {})
    for concept_key, data in user_profile_data.items():
        raw_belief = data.get("belief", [])
        if not isinstance(raw_belief, list) or not all(isinstance(bp, dict) and "a" in bp and "p" in bp for bp in raw_belief):
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

@router.get("/concepts", response_model=Dict[str, ConceptMetadata])
async def get_concepts():
    """Returns all concepts from the concepts.json file."""
    return load_concepts_db()

@router.get("/next-question/{user_id}", response_model=DiagnosticQuestion)
async def get_next_question(user_id: str):
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI client not available for question generation. Please set OPENAI_API_KEY.")

    concepts_db = load_concepts_db()
    user_data = user_models.get(user_id, {})
    candidate_concepts = []

    if not concepts_db:
        raise HTTPException(status_code=404, detail="No concepts available in the database. Cannot generate next question.")

    for concept_key, concept_meta_dict in concepts_db.items():
        if not isinstance(concept_meta_dict, dict):
            print(f"Warning (next-question): Concept metadata for '{concept_key}' is not a dictionary. Skipping.")
            continue
        try:
            concept_title = concept_meta_dict.get('title', concept_key)
            concept_description = concept_meta_dict.get('description', f"Concept: {concept_key}")
            concept_difficulty = float(concept_meta_dict.get('difficulty', DEFAULT_NEW_CONCEPT_DIFFICULTY))
        except Exception as e:
            print(f"Warning (next-question): Invalid metadata for concept '{concept_key}' in concepts.json: {e}. Skipping.")
            continue

        user_concept_progress = user_data.get(concept_key, {
            "belief": [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS],
            "attempts": 0
        })
        
        current_belief: List[Dict[str, float]] = user_concept_progress.get("belief", [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS])
        expected_mastery = sum(bp["a"] * bp["p"] for bp in current_belief)

        attempts = user_concept_progress.get("attempts", 0)

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

    candidate_concepts.sort(key=lambda c: (
        c["expected_mastery"],
        abs(c["difficulty"] - IDEAL_DIFFICULTY_TARGET),
        c["attempts"]
    ))
    
    selected_concept_info = candidate_concepts[0]

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

        if question_data.get("concept") != selected_concept_info['key']:
            print(f"Warning (next-question): LLM returned concept '{question_data.get('concept')}', expected '{selected_concept_info['key']}'. Overriding.")
            question_data["concept"] = selected_concept_info['key']
        if question_data.get("correct_answer") not in ["a", "b"]:
            print(f"Warning (next-question): LLM returned invalid correct_answer '{question_data.get('correct_answer')}'. Defaulting to 'a'.")
            question_data["correct_answer"] = "a"
        
        try:
            difficulty = float(question_data.get("difficulty", 0.5))
            if difficulty < 0.1 or difficulty > 0.9:
                print(f"Warning (next-question): Invalid difficulty value {difficulty}. Adjusting to valid range.")
                question_data["difficulty"] = max(0.1, min(0.9, difficulty))
        except (ValueError, TypeError):
            print(f"Warning (next-question): Could not parse difficulty. Using default.")
            question_data["difficulty"] = 0.5
        
        for field_name in ["concept", "question", "option_a", "option_b", "correct_answer", "explanation", "difficulty"]:
            if field_name not in question_data:
                print(f"Warning (next-question): LLM response missing field '{field_name}'. Setting to default/placeholder.")
                if field_name == "difficulty":
                    question_data[field_name] = 0.5
                else:
                    question_data[field_name] = f"Missing field: {field_name}"

        return DiagnosticQuestion(**question_data)
    except Exception as e:
        print(f"Error (next-question): Failed to generate question via OpenAI for concept '{selected_concept_info['title']}': {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to generate question via OpenAI for concept '{selected_concept_info['title']}'. Error: {str(e)}")

@router.get("/next-question-batch/{user_id}", response_model=List[DiagnosticQuestion])
async def get_next_question_batch(user_id: str, count: int = 5):
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI client not available. Please set OPENAI_API_KEY.")
    if count <= 0 or count > 10:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 10.")

    concepts_db = load_concepts_db()
    user_data = user_models.get(user_id, {})
    generated_questions: List[DiagnosticQuestion] = []
    candidate_concepts_for_ranking = []

    if not concepts_db:
        raise HTTPException(status_code=404, detail="No concepts available in the database to generate questions.")

    for concept_key, concept_meta_dict in concepts_db.items():
        if not isinstance(concept_meta_dict, dict):
            print(f"Warning (next-batch): Concept metadata for '{concept_key}' is not a dict. Skipping.")
            continue
        
        try:
            concept_title = concept_meta_dict.get('title', concept_key)
            concept_description = concept_meta_dict.get('description', f"Concept: {concept_key}")
            concept_difficulty = float(concept_meta_dict.get('difficulty', DEFAULT_NEW_CONCEPT_DIFFICULTY))
        except Exception as e:
            print(f"Warning (next-batch): Invalid metadata for '{concept_key}': {e}. Skipping.")
            continue

        user_concept_progress = user_data.get(concept_key, {
            "belief": [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS],
            "attempts": 0
        })
        
        current_belief_for_batch: List[Dict[str, float]] = user_concept_progress.get("belief", [{"a": level, "p": 1.0 / NUM_BELIEF_POINTS} for level in BELIEF_ABILITY_LEVELS])
        expected_mastery_for_batch = sum(bp["a"] * bp["p"] for bp in current_belief_for_batch)
        attempts = user_concept_progress.get("attempts", 0)

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

    candidate_concepts_for_ranking.sort(key=lambda c: (
        c["expected_mastery"],
        abs(c["difficulty"] - IDEAL_DIFFICULTY_TARGET),
        c["attempts"]
    ))

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
        raise HTTPException(status_code=503, detail="Failed to generate any questions for the selected concepts in the batch.")

    return generated_questions 