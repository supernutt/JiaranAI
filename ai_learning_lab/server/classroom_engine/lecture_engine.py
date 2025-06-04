import json
from typing import List, Optional
from openai import OpenAI

from .lecture_prompt import SIMULATED_LECTURE_TEMPLATE
from .models import Message, Turn

# Initialize OpenAI client
# Ensure API key is loaded from environment variables or set directly
# For example, client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
# If your main app initializes it, you might not need to do it here again,
# but ensure it's accessible.
client = OpenAI()

def generate_simulated_lecture(topic: str, previous_summary: Optional[str] = None, mastery_hint: str = "", model: str = "gpt-3.5-turbo-1106") -> List[Turn]:
    context_header = ""
    # Default instruction if no previous summary
    initial_instruction = f"You are simulating a virtual AI classroom about the topic: \"{topic}\"."

    if previous_summary:
        context_header = f"Context of our discussion so far:\n{previous_summary}\n\n---\n"
        initial_instruction = f"Now, building on that, continue the lecture on \"{topic}\"."
    
    # Simple mastery integration - just append to instruction
    if mastery_hint:
        initial_instruction += mastery_hint
    
    # The SIMULATED_LECTURE_TEMPLATE should now correctly use these placeholders.
    # The {topic} placeholder within initial_instruction handles the topic injection.
    final_prompt_text = SIMULATED_LECTURE_TEMPLATE.format(
        context_header=context_header,
        initial_instruction=initial_instruction
    )

    print(f"Sending prompt to OpenAI for topic '{topic}':\n{final_prompt_text}")

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": final_prompt_text}],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        content = resp.choices[0].message.content
        print(f"Raw OpenAI response:\n{content}")
        data = json.loads(content)

        turns: List[Turn] = []
        if "turns" not in data or not isinstance(data["turns"], list):
            print(f"Error: 'turns' key missing or not a list in OpenAI response: {data}")
            return [] 

        for raw_turn in data["turns"]:
            if not isinstance(raw_turn, dict) or "teacher" not in raw_turn or "students" not in raw_turn:
                print(f"Skipping malformed turn: {raw_turn}")
                continue
            
            students = []
            if isinstance(raw_turn["students"], list):
                for s_data in raw_turn["students"]:
                    if isinstance(s_data, dict) and "name" in s_data and "text" in s_data:
                        students.append(Message(author=s_data["name"], text=s_data["text"]))
                    else:
                        print(f"Skipping malformed student data: {s_data}")
            else:
                print(f"Skipping turn due to malformed students field: {raw_turn['students']}")
                continue

            turns.append(Turn(teacher=raw_turn["teacher"], students=students))
        
        return turns
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from OpenAI response: {e}")
        return [] 
    except Exception as e:
        print(f"An unexpected error occurred in generate_simulated_lecture: {e}")
        return [] 