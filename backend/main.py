import base64
import json
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from backend.parser import ParserError, normalize_input
except ImportError:  # pragma: no cover - fallback for local execution from backend/
    from parser import ParserError, normalize_input


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
    return {"status": "ok", "service": "logguard-backend"}


@app.post("/analyze")
def analyze(payload: AnalyzeRequest) -> dict:
    """
    LG-101 endpoint contract stub.
    Pipeline orchestration is intentionally placeholder-only in this ticket.
    """
    try:
        normalized = normalize_input(payload.input_type, payload.content)
    except ParserError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc

    return {
        "summary": "LG-101 scaffold response. Analysis pipeline not implemented yet.",
        "content_type": normalized["content_type"],
        "findings": [],
        "risk_score": 0,
        "risk_level": "low",
        "action": "none",
        "insights": [
            "Endpoint and contracts are in place.",
            "Pipeline modules are scaffolded for LG-102 onward.",
        ],
        "metadata": {
            "normalized_preview": normalized["text"][:80],
            "options": payload.options.model_dump(),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []),
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
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail={"code": "empty_file", "message": "uploaded file is empty"},
        )

    content = _build_file_payload(file, file_bytes)
    options = {
        "mask": mask,
        "block_high_risk": block_high_risk,
        "log_analysis": log_analysis,
    }

    try:
        normalized = normalize_input("file", content)
    except ParserError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc

    return {
        "summary": "LG-102 parser response via file upload endpoint.",
        "content_type": normalized["content_type"],
        "findings": [],
        "risk_score": 0,
        "risk_level": "low",
        "action": "none",
        "insights": [
            "File upload has been parsed and normalized.",
            "Detection/risk/policy engines will be wired in later tickets.",
        ],
        "metadata": {
            "file_name": normalized["metadata"].get("file_name"),
            "file_suffix": normalized["metadata"].get("file_suffix"),
            "line_count": normalized["metadata"].get("line_count", 0),
            "chunk_count": normalized["metadata"].get("chunk_count", 0),
            "warnings": normalized.get("warnings", []),
            "options": options,
        },
    }