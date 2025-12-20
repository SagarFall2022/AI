SYSTEM_PROMPT = """
You extract catalog graph structure from text.

Return JSON exactly:
{
  "parts": [{"number":"", "description":""}],
  "kits": [{"number":"", "includes":["..."], "description":""}],
  "systems": [{"name":""}],
  "replacements": [{"from":"", "to":""}],
  "applies": [{"item":"<part_or_kit_number>", "system":"<system_name>"}]
}

Rules:
- Use ONLY what is explicitly present.
- If unsure, omit.
- Part numbers and kit numbers must be strings.
"""

def extract_graph(llm, text: str) -> dict:
    return llm.json(SYSTEM_PROMPT, text[:6000])
