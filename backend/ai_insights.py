import json
import logging
import os
from typing import Any


logger = logging.getLogger("logguard.workflow")

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


def _build_prompt(context: dict[str, Any]) -> str:
    compact_json = json.dumps(context, ensure_ascii=True, separators=(",", ":"))
    return (
        "You are a security analyst for logs. "
        "Use the provided analyzer context and return a complete security summary. "
        "Include key risks, affected lines or patterns, and concrete remediation steps. "
        "The response can be paragraph or bullet points."
        "\nAnalyzer context JSON:\n"
        f"{compact_json}"
    )


def _build_chat_prompt(message: str, report: dict[str, Any] | None, history: list[dict[str, str]] | None = None) -> str:
    report_json = json.dumps(report or {}, ensure_ascii=True, separators=(",", ":"))
    history_json = json.dumps(history or [], ensure_ascii=True, separators=(",", ":"))
    return (
        "You are LogGuard security assistant. "
        "Answer the user question using the provided report context and conversation history. "
        "Be specific, reference concrete findings where possible, and avoid generic advice."
        "\nConversation history JSON:\n"
        f"{history_json}"
        "\nReport context JSON:\n"
        f"{report_json}"
        "\nUser question:\n"
        f"{message}"
    )


def _call_gemini(prompt: str, api_key: str, model_name: str, timeout_seconds: float) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("gemini_sdk_unavailable") from exc

    _ = timeout_seconds
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=900,
        ),
    )

    text = getattr(response, "text", "")
    if not text:
        raise ValueError("empty_model_response")
    return str(text)


def generate_insights(context: dict[str, Any]) -> list[str]:
    """
    LG-105 simple Gemini integration: pass analyzer context and return raw model summary.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    if not api_key:
        logger.info("workflow=ai_insights step=fallback reason=missing_api_key")
        return ["AI summary unavailable: GEMINI_API_KEY is not configured."]

    prompt = _build_prompt(context)
    try:
        logger.info("workflow=ai_insights step=model_call_started model=%s", model_name)
        raw = _call_gemini(prompt, api_key, model_name, timeout_seconds=10.0)
        summary = raw.strip()
        if not summary:
            raise ValueError("empty_model_response")
        logger.info("workflow=ai_insights step=model_call_completed model=%s", model_name)
        return [summary]
    except Exception as exc:
        logger.warning(
            "workflow=ai_insights step=model_call_failed model=%s error=%s",
            model_name,
            str(exc),
        )
        return ["AI summary unavailable: model call failed."]


def generate_chat_response(
    message: str,
    report: dict[str, Any] | None,
    history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL

    if not api_key:
        logger.info("workflow=chat_llm step=fallback reason=missing_api_key")
        return "Chat assistant unavailable: GEMINI_API_KEY is not configured."

    prompt = _build_chat_prompt(message, report, history)
    try:
        logger.info("workflow=chat_llm step=model_call_started model=%s", model_name)
        raw = _call_gemini(prompt, api_key, model_name, timeout_seconds=10.0)
        answer = raw.strip()
        if not answer:
            raise ValueError("empty_model_response")
        logger.info("workflow=chat_llm step=model_call_completed model=%s", model_name)
        return answer
    except Exception as exc:
        logger.warning(
            "workflow=chat_llm step=model_call_failed model=%s error=%s",
            model_name,
            str(exc),
        )
        return "Chat assistant unavailable: model call failed."
