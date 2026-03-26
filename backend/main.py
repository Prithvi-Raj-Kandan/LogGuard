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
    from backend.ai_insights import generate_chat_response, generate_insights
    from backend.log_analyzer import analyze_log_lines
    from backend.parser import ParserError, normalize_input
    from backend.patterns import detect_patterns_in_lines, identify_log_type
    from backend.policy_engine import apply_policy
    from backend.risk_engine import calculate_risk
except ImportError:  # pragma: no cover - fallback for local execution from backend/
    from ai_insights import generate_chat_response, generate_insights
    from log_analyzer import analyze_log_lines
    from parser import ParserError, normalize_input
    from patterns import detect_patterns_in_lines, identify_log_type
    from policy_engine import apply_policy
    from risk_engine import calculate_risk


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
    history: list[dict[str, str]] | None = None


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
        "workflow=chat step=request_received message_length=%d has_report=%s report_id=%s history_count=%d",
        len(payload.message),
        bool(payload.report),
        payload.report_id or "none",
        len(payload.history or []),
    )
    response = generate_chat_response(payload.message, payload.report, payload.history)
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

    logger.info("workflow=analyze request_id=%s step=risk_scoring_started", request_id)
    risk_result = calculate_risk(findings)
    logger.info(
        "workflow=analyze request_id=%s step=risk_scoring_completed risk_score=%d risk_level=%s",
        request_id,
        int(risk_result.get("risk_score", 0)),
        str(risk_result.get("risk_level", "low")),
    )

    logger.info("workflow=analyze request_id=%s step=policy_engine_started", request_id)
    policy_result = apply_policy(
        normalized.get("text", ""),
        findings,
        payload.options.mask,
        block_high_risk=payload.options.block_high_risk,
        risk_level=str(risk_result.get("risk_level", "low")),
    )
    logger.info(
        "workflow=analyze request_id=%s step=policy_engine_completed action=%s warnings=%d",
        request_id,
        str(policy_result.get("action", "none")),
        len(policy_result.get("warnings", [])),
    )

    logger.info("workflow=analyze request_id=%s step=ai_insights_started", request_id)
    analyzer_context = analyzer_result or {
        "line_count": normalized["metadata"].get("line_count", 0),
        "findings": findings,
        "grouped_findings": {},
        "log_profile": log_profile,
        "summary": {
            "total_findings": len(findings),
            "unique_lines_affected": len({int(item.get("line", 0)) for item in findings if int(item.get("line", 0)) > 0}),
        },
    }
    insights = generate_insights(
        {
            "request_id": request_id,
            "content_type": normalized["content_type"],
            "analyzer": analyzer_context,
        }
    )
    logger.info(
        "workflow=analyze request_id=%s step=ai_insights_completed insights=%d",
        request_id,
        len(insights),
    )
    if insights:
        logger.info("workflow=analyze request_id=%s step=ai_summary_content summary=%s", request_id, insights[0])

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
        "risk_score": int(risk_result.get("risk_score", 0)),
        "risk_level": str(risk_result.get("risk_level", "low")),
        "action": str(policy_result.get("action", "none")),
        "insights": insights,
        "processed_content": str(policy_result.get("processed_content", normalized.get("text", ""))),
        "metadata": {
            "normalized_preview": normalized["text"][:80],
            "options": payload.options.model_dump(),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []) + list(policy_result.get("warnings", [])),
            "request_id": request_id,
            "processing_time_ms": elapsed_ms,
            "log_type": log_profile.get("log_type", "unknown"),
            "log_sub_type": log_profile.get("log_sub_type", "unknown"),
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
            "risk_breakdown": risk_result.get("breakdown", {}),
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

    logger.info("workflow=analyze_upload request_id=%s step=risk_scoring_started", request_id)
    risk_result = calculate_risk(findings)
    logger.info(
        "workflow=analyze_upload request_id=%s step=risk_scoring_completed risk_score=%d risk_level=%s",
        request_id,
        int(risk_result.get("risk_score", 0)),
        str(risk_result.get("risk_level", "low")),
    )

    logger.info("workflow=analyze_upload request_id=%s step=policy_engine_started", request_id)
    policy_result = apply_policy(
        normalized.get("text", ""),
        findings,
        mask,
        block_high_risk=block_high_risk,
        risk_level=str(risk_result.get("risk_level", "low")),
    )
    logger.info(
        "workflow=analyze_upload request_id=%s step=policy_engine_completed action=%s warnings=%d",
        request_id,
        str(policy_result.get("action", "none")),
        len(policy_result.get("warnings", [])),
    )

    logger.info("workflow=analyze_upload request_id=%s step=ai_insights_started", request_id)
    analyzer_context = analyzer_result or {
        "line_count": normalized["metadata"].get("line_count", 0),
        "findings": findings,
        "grouped_findings": {},
        "log_profile": log_profile,
        "summary": {
            "total_findings": len(findings),
            "unique_lines_affected": len({int(item.get("line", 0)) for item in findings if int(item.get("line", 0)) > 0}),
        },
    }
    insights = generate_insights(
        {
            "request_id": request_id,
            "content_type": normalized["content_type"],
            "analyzer": analyzer_context,
        }
    )
    logger.info(
        "workflow=analyze_upload request_id=%s step=ai_insights_completed insights=%d",
        request_id,
        len(insights),
    )
    if insights:
        logger.info("workflow=analyze_upload request_id=%s step=ai_summary_content summary=%s", request_id, insights[0])

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
        "risk_score": int(risk_result.get("risk_score", 0)),
        "risk_level": str(risk_result.get("risk_level", "low")),
        "action": str(policy_result.get("action", "none")),
        "insights": insights,
        "processed_content": str(policy_result.get("processed_content", normalized.get("text", ""))),
        "metadata": {
            "file_name": normalized["metadata"].get("file_name"),
            "file_suffix": normalized["metadata"].get("file_suffix"),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []) + list(policy_result.get("warnings", [])),
            "options": options,
            "request_id": request_id,
            "processing_time_ms": elapsed_ms,
            "log_type": log_profile.get("log_type", "unknown"),
            "log_sub_type": log_profile.get("log_sub_type", "unknown"),
            "log_profile": log_profile,
            "grouped_findings": (analyzer_result or {}).get("grouped_findings", {}),
            "risk_breakdown": risk_result.get("breakdown", {}),
        },
    }