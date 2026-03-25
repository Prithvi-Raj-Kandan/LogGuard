import logging
from typing import Any

try:
    from backend.patterns import identify_log_type, detect_patterns_in_lines
except ImportError:  # pragma: no cover - fallback for local execution from backend/
    from patterns import identify_log_type, detect_patterns_in_lines


logger = logging.getLogger("logguard.workflow")


def _split_log_lines(log_text: str) -> list[dict[str, Any]]:
    if not log_text:
        return []

    raw_lines = log_text.splitlines()
    return [
        {
            "line_number": index,
            "text": line,
        }
        for index, line in enumerate(raw_lines, start=1)
    ]


def _clip_snippet(text: str, max_len: int = 180) -> str:
    compact = text.strip()
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 3] + "..."


def _group_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, dict[str, Any]] = {}
    by_severity = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for finding in findings:
        finding_type = str(finding.get("type", "unknown"))
        risk = str(finding.get("risk", "low")).lower()
        line = int(finding.get("line", 0))

        if risk in by_severity:
            by_severity[risk] += 1

        item = by_type.setdefault(
            finding_type,
            {
                "count": 0,
                "risk": risk,
                "lines": [],
            },
        )
        item["count"] += 1
        if line > 0 and line not in item["lines"]:
            item["lines"].append(line)

    for item in by_type.values():
        item["lines"] = sorted(item["lines"])

    return {
        "by_type": dict(sorted(by_type.items(), key=lambda pair: pair[0])),
        "by_severity": by_severity,
    }


def analyze_log_lines(log_text: str) -> dict[str, Any]:
    """
    LG-104 line-by-line log analyzer.

    Returns line-aware findings, evidence snippets, grouped summary statistics,
    and inferred log profile for downstream orchestration.
    """
    logger.info("workflow=log_analyzer step=analysis_started content_length=%d", len(log_text or ""))

    indexed_lines = _split_log_lines(log_text)
    findings = detect_patterns_in_lines(indexed_lines)

    line_map = {
        int(line["line_number"]): str(line["text"])
        for line in indexed_lines
    }
    findings_with_evidence = []
    for finding in findings:
        line_number = int(finding.get("line", 0))
        evidence_text = line_map.get(line_number, "")
        enriched = dict(finding)
        enriched["evidence_snippet"] = _clip_snippet(evidence_text)
        findings_with_evidence.append(enriched)

    grouped = _group_findings(findings_with_evidence)
    log_profile = identify_log_type(log_text)

    line_count = len(indexed_lines)
    unique_lines = sorted(
        {
            int(item.get("line", 0))
            for item in findings_with_evidence
            if int(item.get("line", 0)) > 0
        }
    )

    logger.info(
        "workflow=log_analyzer step=analysis_completed line_count=%d findings=%d unique_lines=%d",
        line_count,
        len(findings_with_evidence),
        len(unique_lines),
    )

    return {
        "line_count": line_count,
        "findings": findings_with_evidence,
        "grouped_findings": grouped,
        "log_profile": log_profile,
        "summary": {
            "total_findings": len(findings_with_evidence),
            "unique_lines_affected": len(unique_lines),
            "line_numbers": unique_lines,
        },
    }
