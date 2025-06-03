"""
Core data structures for the dynamic classroom feature.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Persona:
    """
    A character that can speak in the classroom.

    role: "teacher", "student", or "mascot"
    style_card: a short prompt snippet that guides the LLM
    voice_id: TTS identifier (e.g. OpenAI voice name)
    """

    name: str
    role: str
    style_card: str
    voice_id: str
    avatar_url: str | None = None


@dataclass
class Message:
    """
    A single line of dialogue produced by any persona or the user.
    """

    author: str
    text: str
    ts: float = field(default_factory=time.time)
    audio_url: str | None = None  # filled in once TTS is added


@dataclass
class Turn:
    teacher: str
    students: List[Message]


@dataclass
class ClassroomSession:
    """
    One live classroom instance.  Holds state between turns.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    personas: List[Persona] = field(default_factory=list)
    transcript: List[Message] = field(default_factory=list)
    scores: Dict[str, int] = field(default_factory=dict)
    phase: str = "lecture"  # warmup | lecture | quiz | wrap
    summary: str = ""  # running conversation summary

    # convenience
    def add_msgs(self, msgs: List[Message]) -> None:
        self.transcript.extend(msgs) 