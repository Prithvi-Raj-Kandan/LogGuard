import base64
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")


logger = logging.getLogger("logguard.workflow")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

try:
    from backend.ai_insights import generate_insights
    from backend.log_analyzer import analyze_log_lines
    from backend.parser import ParserError, normalize_input
    from backend.patterns import detect_patterns_in_lines, identify_log_type
except ImportError:  # pragma: no cover - fallback for local execution from backend/
    from ai_insights import generate_insights
    from log_analyzer import analyze_log_lines
    from parser import ParserError, normalize_input
    from patterns import detect_patterns_in_lines, identify_log_type


class AnalyzeOptions(BaseModel):
    mask: bool = True
    block_high_risk: bool = False
    log_analysis: bool = True


class AnalyzeRequest(BaseModel):
    input_type: Literal["text", "file", "sql", "chat", "log"] = Field(
        description="Type of input submitted for analysis."
    )
    content: str = Field(min_length=1, description="Raw payload content.")
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    report_id: str | None = None
    report: dict[str, Any] | None = None


def _build_chat_response(message: str, report: dict[str, Any] | None) -> str:
    query = message.lower()
    if not report:
        return "I do not have report context yet. Upload a log file first, then ask follow-up questions."

    warnings = report.get("warnings", []) if isinstance(report, dict) else []
    risk_breakdown = report.get("riskBreakdown", {}) if isinstance(report, dict) else {}

    if not warnings:
        return "No warnings were found in the current report, so there is no critical breach to prioritize."

    sorted_warnings = sorted(
        warnings,
        key=lambda item: {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }.get(str(item.get("severity", "low")).lower(), 0),
        reverse=True,
    )

    if "most critical" in query or "critical security breach" in query or "highest risk" in query:
        top = sorted_warnings[0]
        lines = top.get("lineNumbers", [])
        line_text = f" at line {', '.join(str(item) for item in lines)}" if lines else ""
        return (
            f"The most critical issue is {top.get('type', 'unknown')} "
            f"({top.get('severity', 'critical')}){line_text}. "
            "Prioritize immediate credential rotation and redaction."
        )

    if "3 critical" in query or "three critical" in query or "top 3" in query:
        top_three = sorted_warnings[:3]
        details = []
        for index, warning in enumerate(top_three, start=1):
            lines = warning.get("lineNumbers", [])
            line_text = f"line {', '.join(str(item) for item in lines)}" if lines else "line unknown"
            details.append(
                f"{index}. {warning.get('type', 'unknown')} ({warning.get('severity', 'low')}) on {line_text}"
            )
        return "Top 3 highest-priority warnings:\n" + "\n".join(details)

    if "summary" in query or "risk breakdown" in query or "overview" in query:
        return (
            "Risk summary: "
            f"critical={risk_breakdown.get('critical', 0)}, "
            f"high={risk_breakdown.get('high', 0)}, "
            f"medium={risk_breakdown.get('medium', 0)}, "
            f"low={risk_breakdown.get('low', 0)}. "
            f"Total warnings={len(warnings)}."
        )

    top = sorted_warnings[0]
    return (
        "I am using the uploaded report context. "
        f"Start with {top.get('type', 'unknown')} ({top.get('severity', 'low')}) and I can walk you through all findings."
    )


app = FastAPI(
    title="LogGuard API",
    version="0.1.0",
    description="LG-101 scaffold for the AI Secure Data Intelligence Platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
def health() -> dict[str, str]:
    logger.info("workflow=health_check step=completed")
    return {"status": "ok", "service": "logguard-backend"}


@app.post("/chat")
def chat(payload: ChatRequest) -> dict[str, str]:
    logger.info(
        "workflow=chat step=request_received message_length=%d has_report=%s report_id=%s",
        len(payload.message),
        bool(payload.report),
        payload.report_id or "none",
    )
    response = _build_chat_response(payload.message, payload.report)
    logger.info("workflow=chat step=response_ready response_length=%d", len(response))
    return {"response": response}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    """
    LG-101 endpoint contract stub.
    Pipeline orchestration is intentionally placeholder-only in this ticket.
    """
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    logger.info(
        "workflow=analyze request_id=%s step=request_received input_type=%s content_length=%d",
        request_id,
        payload.input_type,
        len(payload.content),
    )

    try:
        logger.info("workflow=analyze request_id=%s step=normalize_input_started", request_id)
        normalized = normalize_input(payload.input_type, payload.content)
        logger.info(
            "workflow=analyze request_id=%s step=normalize_input_completed line_count=%d chunk_count=%d",
            request_id,
            normalized["metadata"].get("line_count", 0),
            normalized["metadata"].get("chunk_count", 0),
        )
    except ParserError as exc:
        logger.warning(
            "workflow=analyze request_id=%s step=normalize_input_failed code=%s message=%s",
            request_id,
            exc.code,
            str(exc),
        )
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc

    logger.info("workflow=analyze request_id=%s step=pattern_detection_started", request_id)
    findings = detect_patterns_in_lines(normalized.get("lines", []))
    logger.info(
        "workflow=analyze request_id=%s step=pattern_detection_completed findings=%d",
        request_id,
        len(findings),
    )

    logger.info("workflow=analyze request_id=%s step=log_type_classification_started", request_id)
    log_profile = identify_log_type(normalized.get("text", ""))
    logger.info(
        "workflow=analyze request_id=%s step=log_type_classification_completed log_type=%s log_sub_type=%s confidence=%.2f",
        request_id,
        log_profile.get("log_type", "unknown"),
        log_profile.get("log_sub_type", "unknown"),
        float(log_profile.get("confidence", 0.0)),
    )

    analyzer_result: dict[str, Any] | None = None
    if payload.options.log_analysis:
        logger.info("workflow=analyze request_id=%s step=log_analyzer_started", request_id)
        analyzer_result = analyze_log_lines(normalized.get("text", ""))
        findings = analyzer_result.get("findings", findings)
        log_profile = analyzer_result.get("log_profile", log_profile)
        logger.info(
            "workflow=analyze request_id=%s step=log_analyzer_completed findings=%d",
            request_id,
            len(findings),
        )

    logger.info("workflow=analyze request_id=%s step=ai_insights_started", request_id)
    insights = generate_insights(
        {
            "request_id": request_id,
            "content_type": normalized["content_type"],
            "line_count": normalized["metadata"].get("line_count", 0),
            "findings": findings,
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
        }
    )
    logger.info(
        "workflow=analyze request_id=%s step=ai_insights_completed insights=%d",
        request_id,
        len(insights),
    )

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "workflow=analyze request_id=%s step=response_ready elapsed_ms=%d",
        request_id,
        elapsed_ms,
    )

    return {
        "summary": "LG-103 detection response.",
        "content_type": normalized["content_type"],
        "findings": findings,
        "risk_score": 0,
        "risk_level": "low",
        "action": "none",
        "insights": insights,
        "metadata": {
            "normalized_preview": normalized["text"][:80],
            "options": payload.options.model_dump(),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []),
            "request_id": request_id,
            "processing_time_ms": elapsed_ms,
            "log_type": log_profile.get("log_type", "unknown"),
            "log_sub_type": log_profile.get("log_sub_type", "unknown"),
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
        },
    }


def _build_file_payload(uploaded_file: UploadFile, file_bytes: bytes) -> str:
    payload: dict[str, Any] = {
        "file_name": uploaded_file.filename or "uploaded_file",
        "mime_type": uploaded_file.content_type,
        "content_base64": base64.b64encode(file_bytes).decode("utf-8"),
    }
    return json.dumps(payload)


@app.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    mask: bool = Form(True),
    block_high_risk: bool = Form(False),
    log_analysis: bool = Form(True),
) -> dict:
    """
    Swagger-friendly multipart endpoint.
    Converts uploaded file into the LG-102 parser payload and reuses normalize_input.
    """
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    logger.info(
        "workflow=analyze_upload request_id=%s step=request_received file_name=%s content_type=%s",
        request_id,
        file.filename or "uploaded_file",
        file.content_type or "unknown",
    )

    logger.info("workflow=analyze_upload request_id=%s step=file_read_started", request_id)
    file_bytes = await file.read()
    logger.info(
        "workflow=analyze_upload request_id=%s step=file_read_completed bytes=%d",
        request_id,
        len(file_bytes),
    )
    if not file_bytes:
        logger.warning(
            "workflow=analyze_upload request_id=%s step=file_validation_failed reason=empty_file",
            request_id,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": "empty_file", "message": "uploaded file is empty"},
        )

    logger.info("workflow=analyze_upload request_id=%s step=build_file_payload_started", request_id)
    content = _build_file_payload(file, file_bytes)
    logger.info("workflow=analyze_upload request_id=%s step=build_file_payload_completed", request_id)
    options = {
        "mask": mask,
        "block_high_risk": block_high_risk,
        "log_analysis": log_analysis,
    }

    try:
        logger.info("workflow=analyze_upload request_id=%s step=normalize_input_started", request_id)
        normalized = normalize_input("file", content)
        logger.info(
            "workflow=analyze_upload request_id=%s step=normalize_input_completed line_count=%d chunk_count=%d",
            request_id,
            normalized["metadata"].get("line_count", 0),
            normalized["metadata"].get("chunk_count", 0),
        )
    except ParserError as exc:
        logger.warning(
            "workflow=analyze_upload request_id=%s step=normalize_input_failed code=%s message=%s",
            request_id,
            exc.code,
            str(exc),
        )
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc

    logger.info("workflow=analyze_upload request_id=%s step=pattern_detection_started", request_id)
    findings = detect_patterns_in_lines(normalized.get("lines", []))
    logger.info(
        "workflow=analyze_upload request_id=%s step=pattern_detection_completed findings=%d",
        request_id,
        len(findings),
    )

    logger.info("workflow=analyze_upload request_id=%s step=log_type_classification_started", request_id)
    log_profile = identify_log_type(normalized.get("text", ""))
    logger.info(
        "workflow=analyze_upload request_id=%s step=log_type_classification_completed log_type=%s log_sub_type=%s confidence=%.2f",
        request_id,
        log_profile.get("log_type", "unknown"),
        log_profile.get("log_sub_type", "unknown"),
        float(log_profile.get("confidence", 0.0)),
    )

    analyzer_result: dict[str, Any] | None = None
    if log_analysis:
        logger.info("workflow=analyze_upload request_id=%s step=log_analyzer_started", request_id)
        analyzer_result = analyze_log_lines(normalized.get("text", ""))
        findings = analyzer_result.get("findings", findings)
        log_profile = analyzer_result.get("log_profile", log_profile)
        logger.info(
            "workflow=analyze_upload request_id=%s step=log_analyzer_completed findings=%d",
            request_id,
            len(findings),
        )

    logger.info("workflow=analyze_upload request_id=%s step=ai_insights_started", request_id)
    insights = generate_insights(
        {
            "request_id": request_id,
            "content_type": normalized["content_type"],
            "line_count": normalized["metadata"].get("line_count", 0),
            "findings": findings,
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
        }
    )
    logger.info(
        "workflow=analyze_upload request_id=%s step=ai_insights_completed insights=%d",
        request_id,
        len(insights),
    )

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "workflow=analyze_upload request_id=%s step=response_ready elapsed_ms=%d",
        request_id,
        elapsed_ms,
    )

    return {
        "summary": "LG-103 detection response via file upload endpoint.",
        "content_type": normalized["content_type"],
        "findings": findings,
        "risk_score": 0,
        "risk_level": "low",
        "action": "none",
        "insights": insights,
        "metadata": {
            "file_name": normalized["metadata"].get("file_name"),
            "file_suffix": normalized["metadata"].get("file_suffix"),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []),
            "options": options,
            "request_id": request_id,
            "processing_time_ms": elapsed_ms,
            "log_type": log_profile.get("log_type", "unknown"),
            "log_sub_type": log_profile.get("log_sub_type", "unknown"),
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
        },
    }