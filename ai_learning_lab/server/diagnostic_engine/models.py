from pydantic import BaseModel
from typing import List, Literal

class DiagnosticRequest(BaseModel):
    content: str

class DiagnosticQuestion(BaseModel):
    concept: str
    question: str
    option_a: str
    option_b: str
    correct_answer: Literal["a", "b"]
    explanation: str
    difficulty: float = 0.5

class DiagnosticResponse(BaseModel):
    questions: List[DiagnosticQuestion]

class ClassroomRequest(BaseModel):
    topic: str

class Character(BaseModel):
    name: str
    statement: str

class ClassroomResponse(BaseModel):
    discussion: List[Character]

class DiagnosticRequestForResponse(BaseModel):
    user_id: str
    concept: str
    response: Literal["correct", "incorrect", "unsure"]
    difficulty: float = 0.5

class BeliefPoint(BaseModel):
    a: float  # ability level
    p: float  # probability

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