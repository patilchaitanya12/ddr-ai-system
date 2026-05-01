from typing import Dict, List


def generate_ddr(reasoned_data: Dict) -> Dict:
    """
    Convert reasoned analysis → final DDR structure
    """

    final_analysis = reasoned_data.get("final_analysis", [])

    property_summary = set()
    area_observations = []
    root_causes = set()
    severity_list = []
    recommendations = set()
    missing_info = set()
    additional_notes = []

    for area_data in final_analysis:
        area = area_data["area"]
        issues = area_data.get("issues", [])
        analysis = area_data.get("analysis", {})

        # 🔹 Property Summary
        for issue in issues:
            property_summary.add(issue["issue_type"])

        # 🔹 Area Observations
        descriptions = []
        for issue in issues:
            descriptions.extend(issue.get("descriptions", []))

        area_observations.append({
            "area": area,
            "details": " ".join(descriptions) if descriptions else "Not Available",
            "images": []  # we can enhance later
        })

        # 🔹 Root Causes
        for cause in analysis.get("probable_root_cause", []):
            root_causes.add(cause)

        # 🔹 Severity
        severity = analysis.get("severity", {})
        severity_list.append({
            "area": area,
            "severity": severity.get("level", "Unknown"),
            "reason": severity.get("reason", "Not Available")
        })

        # 🔹 Recommendations
        for action in analysis.get("recommended_actions", []):
            recommendations.add(action)

        # 🔹 Missing Info
        for missing in analysis.get("missing_information", []):
            missing_info.add(missing)

        # 🔹 Conflicts → Additional Notes
        for conflict in analysis.get("conflicts", []):
            additional_notes.append(conflict)

    return {
        "property_issue_summary": list(property_summary),
        "area_wise_observations": area_observations,
        "probable_root_cause": list(root_causes),
        "severity_assessment": severity_list,
        "recommended_actions": list(recommendations),
        "additional_notes": additional_notes,
        "missing_or_unclear_information": list(missing_info)
    }