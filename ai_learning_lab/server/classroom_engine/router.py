from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
import logging
from typing import Dict, List, Optional

from .models import ClassroomSession, Message, Turn
from .personas import FIXED_PERSONAS
from .state_store import save, get, cleanup_expired_sessions
from .conversation import next_turn, summarize_to_context
from .lecture_engine import generate_simulated_lecture

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StartReq(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)

class TurnReq(BaseModel):
    userMessage: str = Field(..., min_length=1, max_length=500)

class ScriptRequestBody(BaseModel):
    topic: str = Field(default="General science")
    session_id: Optional[str] = None

router = APIRouter()

@router.post("/start")
async def start(req: StartReq, request: Request):
    """Start a new classroom session with the given topic."""
    logger.info(f"Starting new classroom session with topic: {req.topic}")
    
    # Clean up expired sessions periodically
    expired = cleanup_expired_sessions()
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    # Create new session
    sess = ClassroomSession()
    sess.personas = FIXED_PERSONAS.copy()
    save(sess)
    
    logger.info(f"Created session {sess.id} with {len(sess.personas)} personas")
    
    # Return session info
    return {
        "sessionId": sess.id,
        "roster": [
            {"name": p.name, "role": p.role, "avatarUrl": p.avatar_url}
            for p in sess.personas
        ],
    }

@router.post("/turn/{sess_id}")
async def turn(sess_id: str, req: TurnReq, request: Request):
    """Process a user message in an existing classroom session."""
    # Get session
    sess = get(sess_id)
    if not sess:
        logger.warning(f"Session not found: {sess_id}")
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    logger.info(f"Processing turn for session {sess_id}")
    
    # Generate responses
    try:
        batch = await next_turn(sess, req.userMessage)
        
        # Create a name-to-avatar mapping for quick lookups
        avatar_map = {p.name: p.avatar_url for p in sess.personas}
        
        # Add avatar URLs to messages
        response_messages = []
        for m in batch:
            message_data = {
                "author": m.author,
                "text": m.text,
                "ts": m.ts,
                "audio_url": m.audio_url,
                # Use the avatar map for lookups, with fallback
                "avatar_url": avatar_map.get(m.author)
            }
            response_messages.append(message_data)
        
        return {
            "messages": response_messages,
            "phase": sess.phase,
        }
    except Exception as e:
        logger.exception(f"Error processing turn: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.post("/script")
async def script(body: ScriptRequestBody):
    """
    Body can include { "topic": "Photosynthesis", "session_id": "optional_session_id" }
    Returns → { "turns": [...] }
    """
    topic = body.topic
    session_id = body.session_id
    previous_summary = None
    session: Optional[ClassroomSession] = None

    if session_id:
        session = get(session_id)
        if session:
            previous_summary = session.summary
            logger.info(f"Continuing lecture for session {session_id} on topic '{topic}' with existing summary.")
        else:
            logger.warning(f"Session ID {session_id} provided but session not found. Starting new lecture context.")

    generated_turns = generate_simulated_lecture(topic, previous_summary=previous_summary)

    if not generated_turns:
        logger.error(f"generate_simulated_lecture returned no turns for topic: {topic}")
        # Consider returning an error response or a message indicating failure
        # For now, returning empty turns, frontend handles this by showing an error.
        return {"turns": []}

    # If a session exists, update its transcript and summary
    if session:
        messages_from_turns: List[Message] = []
        for turn_data in generated_turns:
            messages_from_turns.append(Message(author="Jiaran", text=turn_data.teacher))
            messages_from_turns.extend(turn_data.students)
        
        session.add_msgs(messages_from_turns)
        session.summary = summarize_to_context(session.summary, messages_from_turns)
        save(session)
        logger.info(f"Updated session {session_id} with new lecture turns and summary.")

    # Prepare payload for the client
    def as_dict(msg: Message): 
        return {"author": msg.author, "text": msg.text, "ts": msg.ts}
        
    payload = [
        {
            "teacher": t.teacher,
            "students": [as_dict(s) for s in t.students]
        }
        for t in generated_turns
    ]
    return {"turns": payload} 