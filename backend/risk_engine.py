from typing import Any


RISK_WEIGHTS: dict[str, int] = {
    "critical": 10,
    "high": 6,
    "medium": 3,
    "low": 1,
}


def calculate_risk(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """LG-106 weighted risk scoring with deterministic threshold mapping."""
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for finding in findings:
        severity = str(finding.get("risk", "low")).lower()
        if severity not in severity_counts:
            severity = "low"
        severity_counts[severity] += 1

    weighted_score = sum(
        severity_counts[level] * weight for level, weight in RISK_WEIGHTS.items()
    )
    risk_score = min(100, weighted_score)

    if severity_counts["critical"] > 0 or risk_score >= 30:
        risk_level = "critical"
    elif severity_counts["high"] >= 2 or risk_score >= 18:
        risk_level = "high"
    elif severity_counts["medium"] >= 2 or risk_score >= 8:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "breakdown": severity_counts,
    }
