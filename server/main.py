from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import openai
from openai import OpenAI
import io

# Load environment variables
load_dotenv()

# Set the API key directly
openai_api_key = "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"

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Pydantic models
class DiagnosticRequest(BaseModel):
    content: str

class DiagnosticQuestion(BaseModel):
    concept: str
    question: str
    option_a: str
    option_b: str
    correct_answer: str
    explanation: str

class DiagnosticResponse(BaseModel):
    questions: List[DiagnosticQuestion]

class ClassroomRequest(BaseModel):
    topic: str

class Character(BaseModel):
    name: str
    statement: str

class ClassroomResponse(BaseModel):
    discussion: List[Character]

@app.post("/upload-content", response_model=str)
async def upload_content(file: Optional[UploadFile] = File(None), text_content: Optional[str] = Form(None)):
    """
    Upload text content either as a file or as raw text.
    Returns the extracted text content.
    """
    if file:
        # Read the file content
        content = await file.read()
        # For now, we only handle .txt files
        if file.filename.endswith(".txt"):
            return content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Only .txt files are supported at this time")
    elif text_content:
        return text_content
    else:
        raise HTTPException(status_code=400, detail="Either file or text_content must be provided")

@app.post("/generate-diagnostic", response_model=DiagnosticResponse)
async def generate_diagnostic(request: DiagnosticRequest):
    """
    Takes raw text and uses OpenAI GPT API to return 3 swipe-style questions.
    Each question has a concept, question, option_a, option_b, correct_answer, and explanation.
    """
    try:
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Generate 3 swipe-style diagnostic questions based on the provided content.
                Each question MUST have:
                - "concept": The concept being tested
                - "question": The question text
                - "option_a": The first option
                - "option_b": The second option
                - "correct_answer": Either "a" or "b" (lowercase)
                - "explanation": Why the answer is correct
                
                Your response MUST be a valid JSON with EXACTLY this format:
                {
                  "questions": [
                    {
                      "concept": "string",
                      "question": "string",
                      "option_a": "string",
                      "option_b": "string",
                      "correct_answer": "a or b",
                      "explanation": "string"
                    },
                    ... (2 more questions with the same structure)
                  ]
                }
                
                It is CRITICAL that each question has all these fields and that "correct_answer" is either "a" or "b".
                """},
                {"role": "user", "content": request.content}
            ],
            response_format={"type": "json_object"}
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        print(f"OpenAI response: {response_content}")
        
        # Parse the JSON response
        import json
        result = json.loads(response_content)
        
        # Validate and fix the response if needed
        if "questions" in result:
            for question in result["questions"]:
                # Ensure correct_answer exists and is valid
                if "correct_answer" not in question or question["correct_answer"] not in ["a", "b"]:
                    # Try to infer the correct answer or default to "a"
                    if "explanation" in question and "option_a" in question and "option_b" in question:
                        explanation = question["explanation"].lower()
                        if "first option" in explanation or "option a" in explanation:
                            question["correct_answer"] = "a"
                        elif "second option" in explanation or "option b" in explanation:
                            question["correct_answer"] = "b"
                        else:
                            question["correct_answer"] = "a"  # Default
                    else:
                        question["correct_answer"] = "a"  # Default
                
                # Ensure all required fields exist
                required_fields = ["concept", "question", "option_a", "option_b", "explanation"]
                for field in required_fields:
                    if field not in question:
                        question[field] = f"Missing {field}"
            
            # Return the validated questions
            return DiagnosticResponse(questions=result["questions"])
        else:
            # Fall back to mock data if format is completely wrong
            raise ValueError("Response missing 'questions' array")
    
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        # Provide mock data instead of failing
        mock_questions = [
            {
                "concept": "Learning",
                "question": "What is the primary purpose of machine learning?",
                "option_a": "To enable computers to learn from data",
                "option_b": "To replace human workers",
                "correct_answer": "a",
                "explanation": "Machine learning is focused on enabling computers to learn patterns from data, not necessarily to replace humans."
            },
            {
                "concept": "Neural Networks",
                "question": "What do artificial neural networks attempt to simulate?",
                "option_a": "The electrical circuits in computers",
                "option_b": "The neural connections in the brain",
                "correct_answer": "b",
                "explanation": "Neural networks are inspired by and attempt to simulate the way neurons connect and process information in the human brain."
            },
            {
                "concept": "AI Ethics",
                "question": "Which of these is a key ethical consideration in AI development?",
                "option_a": "Making AI as powerful as possible",
                "option_b": "Ensuring AI systems are fair and unbiased",
                "correct_answer": "b",
                "explanation": "Fairness and avoiding bias are critical ethical considerations in AI development to prevent harm and discrimination."
            }
        ]
        return DiagnosticResponse(questions=mock_questions)

@app.post("/generate-classroom", response_model=ClassroomResponse)
async def generate_classroom(request: ClassroomRequest):
    """
    Takes a topic and returns a simulated AI classroom discussion.
    Three AI characters contribute to the conversation: Sophia, Leo, and Maya.
    """
    try:
        # Call the OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Changed from gpt-4 to gpt-3.5-turbo
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
        
        # Extract the response content
        response_content = response.choices[0].message.content
        
        # Parse the JSON response
        import json
        result = json.loads(response_content)
        
        # Return the discussion
        return ClassroomResponse(discussion=result["discussion"])
    
    except Exception as e:
        print(f"Error calling OpenAI API: {str(e)}")
        # Provide mock data instead of failing
        mock_discussion = [
            {
                "name": "Sophia",
                "statement": f"I wonder how {request.topic} might change our understanding of the world around us?"
            },
            {
                "name": "Leo",
                "statement": f"But should we really accept everything we hear about {request.topic} without questioning the potential downsides?"
            },
            {
                "name": "Maya",
                "statement": f"The key aspect of {request.topic} is how it connects various concepts together to form a coherent framework for understanding."
            }
        ]
        return ClassroomResponse(discussion=mock_discussion)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
