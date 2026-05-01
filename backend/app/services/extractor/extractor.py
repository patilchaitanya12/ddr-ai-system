import json
from typing import Dict

from groq import Groq

from backend.app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def _build_extraction_prompt(inspection_text: str, thermal_text: str) -> str:
    """
    Create a strict prompt for structured extraction
    """

    return f"""
You are an expert building inspection analyst.

Extract structured observations from the given data.

IMPORTANT RULES:
- Do NOT invent information
- If something is missing → ignore it
- Keep output STRICT JSON only
- No explanations, no extra text

OUTPUT FORMAT:
{{
  "observations": [
    {{
      "area": "",
      "sub_area": "",
      "issue_type": "",
      "description": "",
      "source": "inspection"
    }}
  ],
  "thermal_readings": [
    {{
      "area": "",
      "hotspot_temp": "",
      "coldspot_temp": "",
      "interpretation": ""
    }}
  ]
}}

INSPECTION DATA:
{inspection_text[:8000]}

THERMAL DATA:
{thermal_text[:8000]}
"""
    

def extract_structured_data(parsed_data: Dict) -> Dict:
    """
    Convert raw parsed data → structured schema using LLM
    """

    inspection_text = parsed_data["inspection"]["text"]
    thermal_text = parsed_data["thermal"]["text"]

    prompt = _build_extraction_prompt(inspection_text, thermal_text)

    response = client.chat.completions.create(
        model="llama3-70b-8192",  # fast + good quality
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  # reduce hallucination
    )

    raw_output = response.choices[0].message.content

    try:
        structured_data = json.loads(raw_output)
    except json.JSONDecodeError:
        # fallback safety
        structured_data = {
            "observations": [],
            "thermal_readings": [],
            "error": "Failed to parse LLM output"
        }

    return structured_data