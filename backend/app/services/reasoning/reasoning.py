import json
from typing import Dict

from groq import Groq
from backend.app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def _build_reasoning_prompt(area_data: Dict) -> str:
    return f"""
You are an expert structural inspection analyst.

Analyze the following area data and provide:

1. Severity (Low / Medium / High) with reason
2. Probable root causes
3. Recommended actions
4. Missing or unclear information
5. Any conflicts in data

STRICT RULES:
- Do NOT invent facts
- Base reasoning ONLY on given data
- If data missing → say "Not Available"
- Output STRICT JSON

OUTPUT FORMAT:
{{
  "severity": {{
    "level": "",
    "reason": ""
  }},
  "probable_root_cause": [],
  "recommended_actions": [],
  "missing_information": [],
  "conflicts": []
}}

DATA:
{json.dumps(area_data, indent=2)}
"""


def _run_llm_reasoning(area_data: Dict) -> Dict:
    prompt = _build_reasoning_prompt(area_data)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    raw_output = response.choices[0].message.content

    try:
        return json.loads(raw_output)
    except:
        return {
            "severity": {"level": "Unknown", "reason": "Parsing failed"},
            "probable_root_cause": [],
            "recommended_actions": [],
            "missing_information": ["LLM output parsing failed"],
            "conflicts": []
        }


def run_reasoning(merged_data: Dict) -> Dict:
    """
    Apply reasoning per area
    """

    results = []

    for area in merged_data.get("area_analysis", []):
        reasoning = _run_llm_reasoning(area)

        results.append({
            "area": area["area"],
            "issues": area["issues"],
            "thermal": area["thermal"],
            "analysis": reasoning
        })

    return {
        "final_analysis": results
    }