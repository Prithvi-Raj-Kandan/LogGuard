import json
import logging
import os
import re
import time
from typing import Any


logger = logging.getLogger("logguard.workflow")

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
MAX_INSIGHTS = 4


def _compact_context(context: dict[str, Any]) -> dict[str, Any]:
    findings = context.get("findings", [])
    compact_findings = [
        {
            "type": item.get("type", "unknown"),
            "risk": item.get("risk", "low"),
            "line": item.get("line", 0),
        }
        for item in findings[:12]
    ]

    return {
        "request_id": context.get("request_id"),
        "content_type": context.get("content_type", "unknown"),
        "line_count": int(context.get("line_count", 0)),
        "finding_count": len(findings),
        "log_profile": context.get("log_profile", {}),
        "grouped_findings": context.get("grouped_findings", {}),
        "findings": compact_findings,
    }


def _build_prompt(context: dict[str, Any]) -> str:
    compact = _compact_context(context)
    compact_json = json.dumps(compact, ensure_ascii=True, separators=(",", ":"))
    return (
        "You are a security analyst for application logs. "
        "Understand the context and summarize exactly 3 actionable insights as points. "
        "Each line must be focused on concrete risk and remediation. "
        "Use this context JSON:\n"
        f"{compact_json}"
    )


def _sanitize_insights(raw_text: str) -> list[str]:
    lines = []
    for raw_line in raw_text.splitlines():
        cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", raw_line).strip()
        if not cleaned:
            continue
        cleaned = cleaned[:160]
        lines.append(cleaned)

    unique: list[str] = []
    for line in lines:
        if line not in unique:
            unique.append(line)
    return unique[:MAX_INSIGHTS]


def _fallback_insights(context: dict[str, Any]) -> list[str]:
    findings = context.get("findings", [])
    log_profile = context.get("log_profile", {})
    grouped = context.get("grouped_findings", {})
    by_severity = grouped.get("by_severity", {}) if isinstance(grouped, dict) else {}
    critical_count = int(by_severity.get("critical", 0) or 0)
    high_count = int(by_severity.get("high", 0) or 0)

    if not findings:
        return [
            "No sensitive patterns detected in this input.",
            "Continue monitoring and enforce least-privilege logging practices.",
            "Retain parser and pattern coverage checks in CI to prevent regressions.",
        ]

    return [
        (
            "Prioritize secret rotation for critical findings "
            f"(critical={critical_count}, high={high_count})."
        ),
        (
            "Detected log profile: "
            f"{log_profile.get('log_type', 'unknown')}/{log_profile.get('log_sub_type', 'unknown')}."
        ),
        "Apply redaction hints before storage or forwarding logs to external systems.",
    ]


def _call_gemini(prompt: str, api_key: str, model_name: str, timeout_seconds: float) -> str:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("gemini_sdk_unavailable") from exc

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 220,
            },
            request_options={"timeout": timeout_seconds},
        )
    except TypeError:
        # Some SDK versions may not support request_options.
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 220,
            },
        )

    text = getattr(response, "text", "")
    if not text:
        raise ValueError("empty_model_response")
    return str(text)


def generate_insights(context: dict[str, Any]) -> list[str]:
    """
    LG-105 Gemini integration with schema validation and deterministic fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    if not api_key:
        logger.info("workflow=ai_insights step=fallback reason=missing_api_key")
        return _fallback_insights(context)

    prompt = _build_prompt(context)
    attempts = 2
    for attempt in range(1, attempts + 1):
        try:
            logger.info(
                "workflow=ai_insights step=model_call_started model=%s attempt=%d",
                model_name,
                attempt,
            )
            raw = _call_gemini(prompt, api_key, model_name, timeout_seconds=10.0)
            insights = _sanitize_insights(raw)
            if len(insights) < 2:
                raise ValueError("insufficient_insights")

            logger.info(
                "workflow=ai_insights step=model_call_completed model=%s attempt=%d insights=%d",
                model_name,
                attempt,
                len(insights),
            )
            return insights
        except Exception as exc:
            logger.warning(
                "workflow=ai_insights step=model_call_failed model=%s attempt=%d error=%s",
                model_name,
                attempt,
                str(exc),
            )
            if attempt < attempts:
                time.sleep(0.25 * attempt)

    logger.info("workflow=ai_insights step=fallback reason=model_unavailable")
    return _fallback_insights(context)
