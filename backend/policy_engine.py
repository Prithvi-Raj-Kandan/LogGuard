import re
from typing import Any


def _mask_value(value: str, hint: str) -> str:
    if not value:
        return value

    if hint == "mask_all_but_last4":
        if len(value) <= 4:
            return "*" * len(value)
        return "*" * (len(value) - 4) + value[-4:]

    if hint == "mask_partial":
        if len(value) <= 4:
            return "*" * len(value)
        return value[:2] + "*" * (len(value) - 4) + value[-2:]

    if hint == "mask_credentials":
        return re.sub(r":([^:@/\s]+)@", r":***@", value)

    return "[REDACTED]"


def apply_policy(
    content: str,
    findings: list[dict[str, Any]],
    mask: bool,
    *,
    block_high_risk: bool = False,
    risk_level: str = "low",
) -> dict[str, Any]:
    """LG-106 policy behavior: mask and warn; optionally block high-risk payloads."""
    warnings: list[str] = []

    if block_high_risk and risk_level in {"high", "critical"}:
        warnings.append("Request blocked by policy due to high-risk findings.")
        return {
            "action": "blocked",
            "processed_content": "",
            "warnings": warnings,
        }

    processed_content = content
    masked_count = 0

    if mask and findings:
        lines = processed_content.splitlines()
        line_map: dict[int, list[dict[str, Any]]] = {}
        for finding in findings:
            line = int(finding.get("line", 0))
            if line > 0:
                line_map.setdefault(line, []).append(finding)

        for line_number, line_findings in line_map.items():
            if line_number > len(lines):
                continue
            line_text = lines[line_number - 1]
            for finding in line_findings:
                raw_value = str(finding.get("value", ""))
                if not raw_value:
                    continue
                hint = str(finding.get("redaction_hint", "mask_all"))
                replacement = _mask_value(raw_value, hint)
                updated = line_text.replace(raw_value, replacement)
                if updated != line_text:
                    masked_count += 1
                    line_text = updated
            lines[line_number - 1] = line_text

        processed_content = "\n".join(lines)

    action = "masked" if mask and masked_count > 0 else "none"
    if action == "masked":
        warnings.append(f"Applied masking to {masked_count} sensitive values.")

    return {
        "action": action,
        "processed_content": processed_content,
        "warnings": warnings,
    }
