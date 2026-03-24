from typing import Any


RISK_LEVELS: dict[str, str] = {
    "email": "low",
    "phone": "low",
    "token": "high",
    "api_key": "high",
    "password": "critical",
    "stack_trace": "medium",
}


def detect_patterns(text: str) -> list[dict[str, Any]]:
    """
    LG-101 scaffold for regex-based detection.
    LG-103 will implement full pattern matching logic.
    """
    _ = text
    return []
