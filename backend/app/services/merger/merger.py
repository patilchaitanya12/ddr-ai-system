from typing import Dict, List
from collections import defaultdict


def _normalize_text(text: str) -> str:
    """Basic normalization"""
    return text.strip().lower()


def merge_data(structured_data: Dict) -> Dict:
    """
    Merge observations + thermal into area-wise grouped data
    """

    observations = structured_data.get("observations", [])
    thermal_data = structured_data.get("thermal_readings", [])

    area_map = defaultdict(lambda: {
        "issues": [],
        "thermal": None
    })

    #Step 1: Process observations
    for obs in observations:
        area = _normalize_text(obs.get("area", "unknown"))
        issue_type = _normalize_text(obs.get("issue_type", "unknown"))

        # Check if issue already exists
        existing_issue = next(
            (i for i in area_map[area]["issues"] if i["issue_type"] == issue_type),
            None
        )

        if existing_issue:
            # Merge location + description
            if obs.get("sub_area"):
                existing_issue["locations"].add(_normalize_text(obs["sub_area"]))

            existing_issue["descriptions"].append(obs.get("description", ""))

        else:
            # Create new issue entry
            area_map[area]["issues"].append({
                "issue_type": issue_type,
                "locations": set([_normalize_text(obs.get("sub_area", ""))]),
                "descriptions": [obs.get("description", "")],
                "source": obs.get("source", "unknown")
            })

    #Step 2: Attach thermal data
    for therm in thermal_data:
        area = _normalize_text(therm.get("area", "unknown"))

        area_map[area]["thermal"] = {
            "hotspot_temp": therm.get("hotspot_temp"),
            "coldspot_temp": therm.get("coldspot_temp"),
            "interpretation": therm.get("interpretation"),
            "available": True
        }

    #Step 3: Convert sets → lists (JSON safe)
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