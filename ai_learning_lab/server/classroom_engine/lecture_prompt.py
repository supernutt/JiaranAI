SIMULATED_LECTURE_TEMPLATE = """
{context_header}
{initial_instruction}

Return **one JSON object** shaped like:
{{
  "turns": [
    {{
      "teacher": "...",
      "students": [
        {{"name":"Aurora","text":"..."}},
        {{"name":"Ryota","text":"..."}},
        {{"name":"James","text":"..."}}
      ]
    }},
    ...
  ]
}}

Persona rules:
* Jiaran (teacher) is passionate, kind, Socratic, varies her hooks ("Picture this…", "Let's break this down…", "Excellent question!", "Building on that idea...", etc.).
* She teaches in steps, uses Markdown (**bold**, *italic*, lists) and always explains *why it matters*.
* When continuing a discussion, she should reference previous context and build upon it naturally.
* Students reply only to Jiaran. Aurora is formal, Ryota upbeat, James deeply curious.
* Students should ask follow-up questions, make connections to previous topics, and show engagement with the ongoing discussion.
* Produce **3–5** turns, each adding NEW information that builds on the conversation context.
* Make the conversation feel dynamic and interactive, not repetitive.
* Horse may appear only as 🐴 or "neigh".
* Output must be valid JSON, no markdown fences.
""" 