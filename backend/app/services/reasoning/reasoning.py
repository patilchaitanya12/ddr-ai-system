import json
import re
from typing import Dict

from groq import Groq
from backend.app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)


#Extract valid JSON from LLM output
def _extract_json(text: str):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return None


#Prompt Builder
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
- Output STRICT JSON ONLY (no explanation text)

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


# 🤖 Run LLM reasoning
def _run_llm_reasoning(area_data: Dict) -> Dict:
    prompt = _build_reasoning_prompt(area_data)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  
    )

    raw_output = response.choices[0].message.content

    
    print("------------------ RAW LLM OUTPUT-------------")
    print(raw_output)
    print("-----------------------")

    parsed = _extract_json(raw_output)

    if parsed:
        return parsed
    else:
        return {
            "severity": {"level": "Unknown", "reason": "Parsing failed"},
            "probable_root_cause": [],
            "recommended_actions": [],
            "missing_information": ["LLM output parsing failed"],
            "conflicts": []
        }


#Main reasoning pipeline
def run_reasoning(merged_data: Dict) -> Dict:
    """
    Apply reasoning per area
    """

    results = []

    area_list = merged_data.get("area_analysis", [])

    if not area_list:
        print("No area data for reasoning")
        return {"final_analysis": []}

    for area in area_list:
        reasoning = _run_llm_reasoning(area)

        results.append({
            "area": area.get("area", "unknown"),
            "issues": area.get("issues", []),
            "thermal": area.get("thermal", {}),
            "analysis": reasoning
        })

    return {
        "final_analysis": results
    }