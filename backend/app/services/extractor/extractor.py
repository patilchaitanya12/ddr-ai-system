import json
import re
from typing import Dict

from groq import Groq
from backend.app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def _extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return None


def _build_extraction_prompt(inspection_text: str, thermal_text: str) -> str:
    return f"""
    You are an expert building inspection analyst.
    
    Extract ONLY inspection observations.
    
    IGNORE thermal data for now.
    
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
      "thermal_readings": []
    }}
    
    INSPECTION DATA:
    {inspection_text[:3000]}
    """


def extract_structured_data(parsed_data: Dict) -> Dict:
    inspection_text = parsed_data["inspection"]["text"]
    thermal_text = parsed_data["thermal"]["text"]

    prompt = _build_extraction_prompt(inspection_text, thermal_text)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    raw_output = response.choices[0].message.content

    print("RAW OUTPUT:\n", raw_output)

    structured_data = _extract_json(raw_output)

    if not structured_data:
        print("JSON parsing failed")
        structured_data = {
            "observations": [],
            "thermal_readings": []
        }

    print("FINAL STRUCTURED DATA:", structured_data)
    print("OBS COUNT:", len(structured_data.get("observations", [])))

    return structured_data