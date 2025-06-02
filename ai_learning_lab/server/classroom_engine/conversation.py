"""
Single-turn conversation generator.
Produces teacher + three student replies in ONE OpenAI call to save tokens.
"""

from __future__ import annotations

import json
import os
import logging
import random
from pathlib import Path
from random import sample
from typing import List, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the specific .env file
env_path = "/Users/supphanatanantachaisophon/Desktop/JiaranAI/server/.env"
if Path(env_path).exists():
    logger.info(f"Loading environment variables from {env_path}")
    load_dotenv(env_path)
else:
    logger.warning(f"Environment file not found at {env_path}")

# Try to initialize OpenAI client
try:
    from openai import OpenAI
    
    # Get API key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        client = None
    else:
        logger.info("Initializing OpenAI client with API key")
        client = OpenAI(api_key=api_key)
except (ImportError, Exception) as e:
    logger.warning(f"OpenAI client initialization failed: {e}")
    client = None

from .models import ClassroomSession, Message, Persona
from .personas import FIXED_PERSONAS

SYSTEM_TEMPLATE = """You are simulating a virtual classroom with a teacher and several students.

You must output ONE JSON object exactly like this:
{{
  "teacher": "...",
  "students": [
    {{"name":"Aurora","text":"..."}},
    {{"name":"Ryota","text":"..."}},
    {{"name":"James","text":"..."}}
  ]
}}

### Instructions

* The teacher (Jiaran) gives clear, structured, and educational answers.
* Her responses should:
  - Start with a hook or preview ("Let's break this down…")
  - Use scaffolding techniques (e.g., 1-2-3 steps, analogies, bullet points)
  - Emphasize **why it matters** (real-world relevance)
  - Use light Markdown-style formatting: `**bold**`, `*italic*`, lists, line breaks.
  - Stay friendly and natural, like a favorite teacher—not robotic.
  - IMPORTANT: ALWAYS complete your thoughts and explanations - never end with a colon (:) without providing the promised list or explanation
  - If using a numbered list or steps, always include at least 3 items

* The students should:
  - Respond **only to what Jiaran says** (not the original user message)
  - Ask clarifying questions, react, agree, joke lightly, or suggest next directions
  - Stay in-character and distinct in tone
  - IMPORTANT: Each response must include 3 students

* The Horse only says 'neigh' or 🐴 emoji.

---

Context so far:
{summary}

Recent student comments:
{recent_student_comments}

New user question:
"{user_msg}"

Personas:
{roster}
"""

def _build_system_prompt(session: ClassroomSession, user_msg: str) -> str:
    """Build the system prompt for the OpenAI model using session data."""
    roster_text = "\n".join(
        f"- {p.name} ({p.role}): {p.style_card}" for p in session.personas
    )
    
    # Extract recent student comments to help with meta-questions
    recent_student_comments = []
    # Get last 5 messages from students
    for msg in reversed(session.transcript[-10:]):
        if msg.author != "Jiaran" and msg.author != "User":
            recent_student_comments.append(f"{msg.author}: {msg.text}")
        if len(recent_student_comments) >= 5:
            break
    
    # Reverse to get chronological order
    recent_student_comments.reverse()
    recent_student_text = "\n".join(recent_student_comments) if recent_student_comments else "No recent student comments yet."
    
    return SYSTEM_TEMPLATE.format(
        summary=session.summary.strip(),
        recent_student_comments=recent_student_text,
        user_msg=user_msg.strip(),
        roster=roster_text
    )


def _generate_mock_response(user_message: str, personas: List[Persona]) -> Dict[str, Any]:
    """Generate a mock response when OpenAI client is unavailable."""
    # Find the teacher persona
    teacher = next((p for p in personas if p.role == "teacher"), personas[0])
    
    # Select random student personas (excluding teacher)
    students = [p for p in personas if p.role != "teacher"]
    selected_students = random.sample(students, min(3, len(students)))
    
    # Simple response templates based on common question patterns
    responses = {
        "default": {
            "teacher": f"Let's break this down step by step. The question about '{user_message[:30]}...' is interesting to explore. \n\n**First**, we need to understand the basic concepts. \n\n**Second**, we'll look at how this applies in different contexts. \n\n**Finally**, we'll discuss why this matters in the real world.",
            "students": [
                {"name": s.name, "text": f"I like how you organized that explanation into clear steps!" if s.name != "Horse" else "neigh 🐴"}
                for s in selected_students
            ]
        },
        "math": {
            "teacher": "Let's break this down step by step. **Mathematics** is about understanding patterns and relationships between numbers and concepts.\n\n1. **First**, we identify the key mathematical principles involved\n2. **Next**, we apply specific techniques to solve problems\n3. **Finally**, we interpret our results in context\n\n*Why does this matter?* Mathematical thinking helps us develop logical reasoning skills that apply to many areas of life.",
            "students": [
                {"name": s.name, "text": "I love how math explains the world around us in such a precise way!" if s.name != "Horse" else "neigh 🐴"}
                for s in selected_students
            ]
        },
        "fractions_add": {
            "teacher": "Let's break this down step by step. **Adding fractions** follows a clear process:\n\n1. **Find a common denominator** - The least common multiple (LCM) of the denominators\n2. **Convert both fractions** to equivalent fractions with this common denominator\n3. **Add the numerators** while keeping the denominator the same\n4. **Simplify** the result if possible\n\n*Why does this matter?* Understanding fraction operations is essential for everything from cooking to construction!",
            "students": [
                {"name": "Aurora", "text": "I find it elegant how fractions can be transformed while maintaining their value."},
                {"name": "Ryota", "text": "Converting to a common denominator makes it so much easier to work with fractions!"},
                {"name": "James", "text": "Could we also convert the fractions to decimals to add them?"}
            ]
        },
        "science": {
            "teacher": "Let's break this down step by step. **Science** helps us understand the natural world through:\n\n1. **Observation** - Carefully noting what we see happening\n2. **Hypothesis formation** - Making educated guesses about why things happen\n3. **Experimentation** - Testing our ideas in controlled settings\n4. **Analysis** - Interpreting results to refine our understanding\n\n*Why does this matter?* Scientific thinking helps us make evidence-based decisions in our daily lives.",
            "students": [
                {"name": s.name, "text": "Science is fascinating because it's always evolving with new discoveries!" if s.name != "Horse" else "neigh 🐴"}
                for s in selected_students
            ]
        },
        "photosynthesis": {
            "teacher": "Let's break down **photosynthesis** step by step!\n\n1. **Light Absorption**: Plants capture sunlight using chlorophyll in their leaves\n2. **Water Utilization**: The plant draws water (H₂O) from the soil through its roots\n3. **Carbon Dioxide Conversion**: CO₂ from the air enters through tiny pores called stomata\n4. **Chemical Reaction**: Using light energy, plants convert water and CO₂ into glucose and oxygen\n5. **Energy Storage**: Glucose stores energy for the plant, while oxygen is released into the air\n\n*Why does this matter?* Photosynthesis is the foundation of nearly all food chains and produces the oxygen we breathe!",
            "students": [
                {"name": "Aurora", "text": "The elegance of this process is remarkable. Plants essentially transform sunlight into chemical energy we can consume."},
                {"name": "Ryota", "text": "Wow! So plants are basically solar-powered machines that feed the planet?"},
                {"name": "James", "text": "I'm curious about how much oxygen one tree can produce through this process. Is it enough for a person to breathe?"}
            ]
        }
    }
    
    # Pattern matching for specific questions
    if "photosynthesis" in user_message.lower():
        return responses["photosynthesis"]
    elif "3/4" in user_message and "1/8" in user_message:
        return {
            "teacher": "Let's break down how to add **3/4 + 1/8** step by step.\n\n1. **Find the common denominator**: The LCD of 4 and 8 is 8\n2. **Convert fractions**: 3/4 = 6/8 (multiply by 2/2)\n3. **Add numerators**: 6/8 + 1/8 = 7/8\n\n*Why does this matter?* Understanding fraction addition helps with cooking, construction, and many other real-world measurements!",
            "students": [
                {"name": "Aurora", "text": "The precision of mathematics is quite satisfying. 7/8 is indeed the correct result."},
                {"name": "Ryota", "text": "I like how we convert fractions to the same denominator. It makes addition so clear!"},
                {"name": "James", "text": "This makes me wonder, how would we subtract fractions using the same method?"}
            ]
        }
    elif "2/3" in user_message and "1/6" in user_message:
        return {
            "teacher": "Let's break down adding **2/3 + 1/6** step by step.\n\n1. **Find the common denominator**: The LCD of 3 and 6 is 6\n2. **Convert the first fraction**: 2/3 = 4/6 (multiply by 2/2)\n3. **Add the numerators**: 4/6 + 1/6 = 5/6\n\n*Why does this matter?* Fractions are everywhere in cooking, construction, and financial calculations!",
            "students": [
                {"name": "Victor", "text": "That's a heroic explanation! Finding the common denominator is like uniting different numbers under one banner!"},
                {"name": "Supernut", "text": "I'd say that's a 'fraction-tastic' explanation! These denominators really know how to find common ground!"},
                {"name": "Horse", "text": "neigh 🐴"}
            ]
        }
    elif "denominator" in user_message.lower() and "different" in user_message.lower():
        return {
            "teacher": "Let's break down **adding fractions with different denominators**:\n\n1. **Find the Least Common Multiple (LCM)** of the denominators\n2. **Convert each fraction** to an equivalent fraction with the LCM as denominator\n3. **Add the numerators** while keeping the common denominator\n\n**Example**: For 1/4 + 2/3\n- LCM of 4 and 3 is 12\n- Convert: 1/4 = 3/12 and 2/3 = 8/12\n- Add: 3/12 + 8/12 = 11/12\n\n*Why does this matter?* This skill is essential for cooking, construction, and managing finances!",
            "students": [
                {"name": "Aurora", "text": "The methodology is so elegant. Finding the least common multiple ensures mathematical efficiency."},
                {"name": "James", "text": "I see how this connects to our earlier examples! It's all about finding that common ground."},
                {"name": "Ryota", "text": "This makes fractions much less intimidating when you break it down into these clear steps!"}
            ]
        }
    # Simple topic detection
    elif any(term in user_message.lower() for term in ["fraction", "add", "+"]):
        return responses["fractions_add"]
    elif any(term in user_message.lower() for term in ["math", "equation", "number", "calculation"]):
        return responses["math"]
    elif any(term in user_message.lower() for term in ["science", "experiment", "physics", "chemistry"]):
        return responses["science"]
    else:
        return responses["default"]


def summarize_to_context(existing_summary: str, new_msgs: List[Message]) -> str:
    """
    Create or update the conversation summary based on the latest messages.
    
    Args:
        existing_summary: The current summary of the conversation
        new_msgs: The new messages to incorporate into the summary
        
    Returns:
        Updated summary text
    """
    if client is None:
        # If OpenAI is not available, just return a simple concatenation
        teacher_msg = next((m.text for m in new_msgs if m.author == "Jiaran"), "")
        student_msgs = [f"{m.author}: {m.text}" for m in new_msgs if m.author != "Jiaran"]
        student_summary = "; ".join(student_msgs)
        
        if not existing_summary:
            return f"Discussion about: {teacher_msg[:100]}... Students said: {student_summary[:200]}..."
        return f"{existing_summary}\nTeacher added: {teacher_msg[:100]}...\nStudents added: {student_summary[:200]}..."
    
    try:
        teacher_msg = next((m.text for m in new_msgs if m.author == "Jiaran"), "")
        student_msgs = [f"{m.author}: {m.text}" for m in new_msgs if m.author != "Jiaran"]
        student_summary = "\n".join(student_msgs)
        
        base = f"""Previously:
{existing_summary}

Jiaran just said:
{teacher_msg}

Students just said:
{student_summary}

Update the summary to include both teacher explanations AND important student comments:"""
        
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[{"role":"user", "content": base}],
            temperature=0.4
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.exception(f"Error generating summary: {e}")
        # On error, append a simple marker so we know there was an issue
        teacher_msg = next((m.text for m in new_msgs if m.author == "Jiaran"), "")
        student_msgs = [f"{m.author}: {m.text}" for m in new_msgs if m.author != "Jiaran"]
        student_summary = "; ".join(student_msgs[:3])  # Limit to first 3 for brevity
        return f"{existing_summary}\n[Topic: {teacher_msg[:50]}... Students: {student_summary[:100]}...]"


async def next_turn(
    session: ClassroomSession, user_message: str, *, n_students: int = 3
) -> List[Message]:
    """
    Generate the next turn of conversation based on user input.
    
    Args:
        session: The current classroom session
        user_message: The message from the user
        n_students: Number of student responses to include
        
    Returns:
        List of messages from teacher and students
    """
    # Validate session has personas
    if not session.personas:
        logger.error("Session has no personas defined")
        session.personas = FIXED_PERSONAS.copy()
    
    # For testing without API key, return mock responses
    if client is None:
        logger.info("Using mock responses (OpenAI client not available)")
        payload = _generate_mock_response(user_message, session.personas)
        batch = [Message(author="Jiaran", text=payload["teacher"])]
        
        # Add student messages
        for stu in payload["students"][:n_students]:
            batch.append(Message(author=stu["name"], text=stu["text"]))
        
        session.add_msgs(batch)
        return batch

    try:
        system_prompt = _build_system_prompt(session, user_message)
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=chat_messages,
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        
        content = response.choices[0].message.content
        logger.info(f"OpenAI response: {content}")
        
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            payload = _generate_mock_response(user_message, session.personas)
        
        # Validate required fields
        if "teacher" not in payload or "students" not in payload:
            logger.error(f"OpenAI response missing required fields: {payload}")
            payload = _generate_mock_response(user_message, session.personas)

        # Check if teacher's response ends with a colon and fix if needed
        teacher_text = payload["teacher"]
        if teacher_text.strip().endswith(":"):
            logger.warning("Teacher response ends with a colon without completion")
            # If the message ends with a colon, add appropriate content based on context
            if "photosynthesis" in user_message.lower() or "photosynthesis" in teacher_text.lower():
                teacher_text += "\n\n1. **Oxygen Production**: Photosynthesis releases oxygen into the atmosphere, which all aerobic organisms need to breathe\n2. **Food Chain Foundation**: Plants create glucose, which is the base of nearly all food chains\n3. **Carbon Cycle**: Plants absorb carbon dioxide, helping regulate atmospheric CO₂ levels\n4. **Energy Storage**: The process converts solar energy into chemical energy stored in plants\n\n*This process sustains virtually all life on our planet!*"
            else:
                teacher_text += "\n\n1. **First**, it provides a foundation for understanding the concept\n2. **Second**, it helps us see connections to other related ideas\n3. **Third**, it allows us to apply this knowledge in practical situations\n\n*Understanding this concept helps us make sense of the world around us!*"
            
            payload["teacher"] = teacher_text

        batch: List[Message] = [Message(author="Jiaran", text=payload["teacher"])]

        # Make sure we have student responses
        if not payload["students"] or len(payload["students"]) == 0:
            logger.warning("No student responses in payload, using mock students")
            # Add mock student responses if none were returned
            mock_payload = _generate_mock_response(user_message, session.personas)
            payload["students"] = mock_payload["students"]

        # if model returned more than n_students, trim; if less, fine
        for stu in payload["students"][:n_students]:
            if not isinstance(stu, dict) or "name" not in stu or "text" not in stu:
                logger.error(f"Invalid student entry in OpenAI response: {stu}")
                continue
                
            # Verify student exists in roster
            if not any(p.name == stu["name"] for p in session.personas):
                logger.warning(f"Student {stu['name']} not found in roster, skipping")
                continue
                
            batch.append(Message(author=stu["name"], text=stu["text"]))

        # Ensure we have at least one student response
        if len(batch) <= 1:
            logger.warning("No valid student responses, adding mock responses")
            mock_payload = _generate_mock_response(user_message, session.personas)
            for stu in mock_payload["students"][:n_students]:
                batch.append(Message(author=stu["name"], text=stu["text"]))

        session.add_msgs(batch)
        session.summary = summarize_to_context(session.summary, batch)
        return batch
        
    except Exception as e:
        logger.exception(f"Error in next_turn: {e}")
        # Fall back to mock response on any error
        payload = _generate_mock_response(user_message, session.personas)
        batch = [Message(author="Jiaran", text=payload["teacher"])]
        
        for stu in payload["students"][:n_students]:
            batch.append(Message(author=stu["name"], text=stu["text"]))
            
        session.add_msgs(batch)
        session.summary = summarize_to_context(session.summary, batch)
        return batch 