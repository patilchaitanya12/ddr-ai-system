from typing import Dict
from collections import defaultdict


def _normalize_text(text: str) -> str:
    return text.strip().lower() if text else "unknown"


def _clean_issue_type(issue: str) -> str:
    if not issue:
        return "unknown"

    issue = issue.lower().strip()

    if "damp" in issue:
        return "dampness"
    if "leak" in issue:
        return "leakage"
    if "crack" in issue:
        return "cracks"
    if "seep" in issue:
        return "seepage"
    if "hollow" in issue:
        return "hollowness"
    if "open" in issue or "joint" in issue:
        return "tile defect"

    return issue


def merge_data(structured_data: Dict) -> Dict:
    if "inspection" in structured_data:
        observations = structured_data.get("inspection", {}).get("observations", [])
        thermal_data = structured_data.get("thermal", {}).get("thermal_readings", [])
    else:
        observations = structured_data.get("observations", [])
        thermal_data = structured_data.get("thermal_readings", [])

    area_map = defaultdict(lambda: {
        "issues": [],
        "thermal": None
    })

    for obs in observations:
        # Filter bad entries
        if not obs.get("issue_type") or not obs.get("description"):
            continue

        area = _normalize_text(obs.get("area"))
        issue_type = _clean_issue_type(obs.get("issue_type"))

        existing_issue = next(
            (i for i in area_map[area]["issues"] if i["issue_type"] == issue_type),
            None
        )

        if existing_issue:
            if obs.get("sub_area"):
                existing_issue["locations"].add(_normalize_text(obs["sub_area"]))

            existing_issue["descriptions"].append(obs.get("description", ""))

        else:
            area_map[area]["issues"].append({
                "issue_type": issue_type,
                "locations": set([_normalize_text(obs.get("sub_area", ""))]),
                "descriptions": [obs.get("description", "")],
                "source": obs.get("source", "unknown")
            })

    for therm in thermal_data:
        if not therm.get("area"):
            continue

        area = _normalize_text(therm.get("area"))

        area_map[area]["thermal"] = {
            "hotspot_temp": therm.get("hotspot_temp"),
            "coldspot_temp": therm.get("coldspot_temp"),
            "interpretation": therm.get("interpretation"),
            "available": True
        }

    final_output = []

    for area, data in area_map.items():
        issues_cleaned = []

        for issue in data["issues"]:
            issues_cleaned.append({
                "issue_type": issue["issue_type"],
                "locations": list(issue["locations"]),
                "descriptions": issue["descriptions"],
                "source": issue["source"]
            })

        final_output.append({
            "area": area,
            "issues": issues_cleaned,
            "thermal": data["thermal"] if data["thermal"] else {
                "available": False
            }
        })

    return {
        "area_analysis": final_output
    }