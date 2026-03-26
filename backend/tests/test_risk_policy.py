import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.policy_engine import apply_policy
from backend.risk_engine import calculate_risk


def test_calculate_risk_maps_to_critical_for_critical_findings() -> None:
    findings = [
        {"type": "password", "risk": "critical", "line": 2},
        {"type": "api_key", "risk": "high", "line": 3},
    ]

    result = calculate_risk(findings)

    assert result["risk_score"] == 16
    assert result["risk_level"] == "critical"
    assert result["breakdown"]["critical"] == 1
    assert result["breakdown"]["high"] == 1


def test_calculate_risk_maps_to_medium_without_high_or_critical() -> None:
    findings = [
        {"type": "phone", "risk": "medium", "line": 5},
        {"type": "stack_trace", "risk": "medium", "line": 7},
    ]

    result = calculate_risk(findings)

    assert result["risk_level"] == "medium"
    assert result["risk_score"] == 6


def test_apply_policy_masks_values_when_enabled() -> None:
    content = """user=alice@example.com
password=admin123
Authorization: Bearer abcdefghijklmnop
""".strip()
    findings = [
        {
            "type": "password",
            "value": "password=admin123",
            "risk": "critical",
            "redaction_hint": "mask_all",
            "line": 2,
        },
        {
            "type": "bearer_token",
            "value": "Authorization: Bearer abcdefghijklmnop",
            "risk": "high",
            "redaction_hint": "mask_all",
            "line": 3,
        },
    ]

    result = apply_policy(content, findings, mask=True)

    assert result["action"] == "masked"
    assert "[REDACTED]" in result["processed_content"]
    assert "admin123" not in result["processed_content"]


def test_apply_policy_blocks_when_high_risk_blocking_enabled() -> None:
    content = "api_key=sk-prod-1234567890"
    findings = [{"type": "api_key", "value": "api_key=sk-prod-1234567890", "risk": "high", "line": 1}]

    result = apply_policy(
        content,
        findings,
        mask=True,
        block_high_risk=True,
        risk_level="high",
    )

    assert result["action"] == "blocked"
    assert result["processed_content"] == ""
    assert result["warnings"]
