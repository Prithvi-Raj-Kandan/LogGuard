from typing import Any


def apply_policy(content: str, findings: list[dict[str, Any]], mask: bool) -> dict[str, Any]:
    """
    LG-101 scaffold for policy actions.
    LG-106 will implement masking transformations and warning actions.
    """
    _ = findings
    action = "masked" if mask else "none"
    return {
        "action": action,
        "processed_content": content,
        "warnings": [],
    }
