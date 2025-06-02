"""
Extremely simple in-memory session store.
Swap this out for Redis later.
"""

import time
from typing import Dict, List, Optional

from .models import ClassroomSession

# Session configuration
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Internal storage
_SESSIONS: Dict[str, ClassroomSession] = {}
_LAST_ACCESSED: Dict[str, float] = {}  # Tracks when each session was last accessed


def save(session: ClassroomSession) -> None:
    """Save a session to the store and update its last accessed time."""
    _SESSIONS[session.id] = session
    _LAST_ACCESSED[session.id] = time.time()


def get(session_id: str) -> Optional[ClassroomSession]:
    """Get a session by ID, or None if not found or expired."""
    if session_id not in _SESSIONS:
        return None
    
    # Update last accessed time
    _LAST_ACCESSED[session_id] = time.time()
    return _SESSIONS.get(session_id)


def cleanup_expired_sessions() -> List[str]:
    """Remove expired sessions from the store and return their IDs."""
    current_time = time.time()
    expired_ids = [
        sid for sid, last_accessed in _LAST_ACCESSED.items()
        if current_time - last_accessed > SESSION_TIMEOUT
    ]
    
    for sid in expired_ids:
        if sid in _SESSIONS:
            del _SESSIONS[sid]
        if sid in _LAST_ACCESSED:
            del _LAST_ACCESSED[sid]
    
    return expired_ids 