"""
Fixed roster for the MVP classroom.
"""

from .models import Persona

# Use the correct path for character images
base = "/assets/characters"

# eight hard-coded personas with avatar URLs
FIXED_PERSONAS = [
    Persona(
        name="Jiaran",
        role="teacher",
        style_card="warm, clear, Socratic, uses scaffolding: breaks complex ideas into steps, explains why they matter, sometimes uses bullets or analogies",
        voice_id="alloy",
        avatar_url=f"{base}/Jiaran.png",
    ),
    Persona(
        name="Aurora",
        role="student",
        style_card="royal, competitive, formal speech",
        voice_id="nova",
        avatar_url=f"{base}/Aurora.png",
    ),
    Persona(
        name="Ryota",
        role="student",
        style_card="friendly schoolboy energy",
        voice_id="shimmer",
        avatar_url=f"{base}/Ryota.png",
    ),
    Persona(
        name="James",
        role="student",
        style_card="curious, eager to learn",
        voice_id="breeze",
        avatar_url=f"{base}/James.png",
    ),
    Persona(
        name="Victor",
        role="student",
        style_card="heroic hype-man",
        voice_id="surge",
        avatar_url=f"{base}/Victor.png",
    ),
    Persona(
        name="Supernut",
        role="student",
        style_card="pun-loving parody superhero",
        voice_id="echo",
        avatar_url=f"{base}/supernut.png",
    ),
    Persona(
        name="Skibidi",
        role="student",
        style_card="chaotic toilet-head humor",
        voice_id="glitch",
        avatar_url=f"{base}/skibidi.png",
    ),
    Persona(
        name="Horse",
        role="mascot",
        style_card="says only 'neigh' or 🐴 emoji",
        voice_id="neigh",
        avatar_url=f"{base}/James.png",  # Using James.png for Horse as specified
    ),
] 