import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any, Literal, TypedDict

from docx import Document
from pypdf import PdfReader


class ParserError(ValueError):
	def __init__(self, code: str, message: str):
		super().__init__(message)
		self.code = code


class NormalizedLine(TypedDict):
	line_number: int
	text: str


class NormalizedChunk(TypedDict):
	chunk_id: int
	start_line: int
	end_line: int
	text: str


class NormalizedInput(TypedDict):
	content_type: str
	text: str
	source: str
	lines: list[NormalizedLine]
	chunks: list[NormalizedChunk]
	metadata: dict[str, Any]
	warnings: list[str]


class FilePayload(TypedDict, total=False):
	file_name: str
	mime_type: str
	content_base64: str
	text: str


def _split_lines(text: str) -> list[NormalizedLine]:
	raw_lines = text.splitlines() or [text]
	return [
		{
			"line_number": line_number,
			"text": line,
		}
		for line_number, line in enumerate(raw_lines, start=1)
	]


def _build_chunks(lines: list[NormalizedLine], chunk_size: int) -> list[NormalizedChunk]:
	chunks: list[NormalizedChunk] = []
	if chunk_size <= 0:
		raise ParserError("invalid_chunk_size", "chunk_size must be greater than zero")

	for idx in range(0, len(lines), chunk_size):
		subset = lines[idx : idx + chunk_size]
		if not subset:
			continue

		chunks.append(
			{
				"chunk_id": (idx // chunk_size) + 1,
				"start_line": subset[0]["line_number"],
				"end_line": subset[-1]["line_number"],
				"text": "\n".join(line["text"] for line in subset),
			}
		)

	return chunks


def _decode_base64(content_base64: str) -> bytes:
	try:
		return base64.b64decode(content_base64, validate=True)
	except Exception as exc:
		raise ParserError("invalid_base64", "file content_base64 is invalid") from exc


def _extract_text_from_pdf(file_bytes: bytes) -> str:
	try:
		reader = PdfReader(BytesIO(file_bytes))
	except Exception as exc:
		raise ParserError("pdf_parse_error", "unable to parse PDF file") from exc

	pages: list[str] = []
	for page in reader.pages:
		pages.append(page.extract_text() or "")
	return "\n".join(pages).strip()


def _extract_text_from_docx(file_bytes: bytes) -> str:
	try:
		doc = Document(BytesIO(file_bytes))
	except Exception as exc:
		raise ParserError("doc_parse_error", "unable to parse DOC/DOCX file") from exc

	return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()


def _extract_file_text(file_payload: FilePayload) -> tuple[str, str, list[str], dict[str, Any]]:
	warnings: list[str] = []
	file_name = file_payload.get("file_name", "uploaded_file")
	suffix = Path(file_name).suffix.lower()
	metadata: dict[str, Any] = {
		"file_name": file_name,
		"mime_type": file_payload.get("mime_type"),
		"file_suffix": suffix,
	}

	if file_payload.get("text"):
		text = str(file_payload["text"]).strip()
		content_type = "logs" if suffix == ".log" else "file"
		metadata["extraction_method"] = "inline_text"
		return text, content_type, warnings, metadata

	content_base64 = file_payload.get("content_base64")
	if not content_base64:
		raise ParserError(
			"missing_file_payload",
			"file input requires either text or content_base64 in payload",
		)

	file_bytes = _decode_base64(content_base64)
	metadata["byte_size"] = len(file_bytes)

	if suffix in {".txt", ".log", ".sql", ".csv", ".json"}:
		try:
			text = file_bytes.decode("utf-8")
		except UnicodeDecodeError:
			text = file_bytes.decode("latin-1")
			warnings.append("decoded_non_utf8_text")

		content_type = "logs" if suffix == ".log" else "file"
		metadata["extraction_method"] = "text_decode"
		return text.strip(), content_type, warnings, metadata

	if suffix == ".pdf":
		text = _extract_text_from_pdf(file_bytes)
		metadata["extraction_method"] = "pypdf"
		return text, "file", warnings, metadata

	if suffix in {".docx", ".doc"}:
		if suffix == ".doc":
			warnings.append("legacy_doc_best_effort_parse")
		text = _extract_text_from_docx(file_bytes)
		metadata["extraction_method"] = "python-docx"
		return text, "file", warnings, metadata

	raise ParserError("unsupported_file_type", f"unsupported file extension: {suffix or 'unknown'}")


def _parse_file_payload(content: str) -> FilePayload:
	try:
		parsed = json.loads(content)
	except json.JSONDecodeError as exc:
		raise ParserError(
			"invalid_file_payload",
			"file input must be a JSON payload with file_name and content_base64/text",
		) from exc

	if not isinstance(parsed, dict):
		raise ParserError("invalid_file_payload", "file payload must be a JSON object")
	return parsed


def normalize_input(
	input_type: Literal["text", "file", "sql", "chat", "log"],
	content: str,
	*,
	chunk_size: int = 50,
) -> NormalizedInput:
	"""
	LG-102 parser implementation.

	For input_type="file", content must be JSON:
	{
	  "file_name": "app.log|report.pdf|notes.docx",
	  "content_base64": "..."
	}
	or
	{
	  "file_name": "raw.log",
	  "text": "..."
	}
	"""
	if not content:
		raise ParserError("empty_content", "input content cannot be empty")

	warnings: list[str] = []
	metadata: dict[str, Any] = {"chunk_size": chunk_size, "input_type": input_type}

	if input_type == "file":
		file_payload = _parse_file_payload(content)
		text, normalized_type, file_warnings, file_metadata = _extract_file_text(file_payload)
		warnings.extend(file_warnings)
		metadata.update(file_metadata)
	else:
		normalized_type = "logs" if input_type == "log" else input_type
		text = content.strip()
		metadata["extraction_method"] = "inline_text"

	lines = _split_lines(text)
	chunks = _build_chunks(lines, chunk_size)

	metadata["line_count"] = len(lines)
	metadata["chunk_count"] = len(chunks)

	return {
		"content_type": normalized_type,
		"text": text,
		"source": "inline" if input_type != "file" else "file",
		"lines": lines,
		"chunks": chunks,
		"metadata": metadata,
		"warnings": warnings,
	}
