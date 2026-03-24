import base64
import json
import sys
from pathlib import Path

import pytest

# Allow running pytest from backend/tests without PYTHONPATH tweaks.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.parser import ParserError, normalize_input


def test_normalize_text_chunks_with_line_numbers() -> None:
    content = "line-1\nline-2\nline-3"

    normalized = normalize_input("text", content, chunk_size=2)

    assert normalized["content_type"] == "text"
    assert len(normalized["lines"]) == 3
    assert normalized["lines"][0]["line_number"] == 1
    assert normalized["lines"][2]["line_number"] == 3
    assert len(normalized["chunks"]) == 2
    assert normalized["chunks"][0]["start_line"] == 1
    assert normalized["chunks"][0]["end_line"] == 2
    assert normalized["chunks"][1]["start_line"] == 3


def test_normalize_file_payload_text_base64() -> None:
    raw_text = "alpha\nbeta"
    payload = {
        "file_name": "app.log",
        "content_base64": base64.b64encode(raw_text.encode("utf-8")).decode("utf-8"),
    }

    normalized = normalize_input("file", json.dumps(payload), chunk_size=10)

    assert normalized["source"] == "file"
    assert normalized["content_type"] == "logs"
    assert normalized["text"] == raw_text
    assert normalized["metadata"]["file_suffix"] == ".log"


def test_invalid_base64_raises_parser_error() -> None:
    payload = {
        "file_name": "bad.txt",
        "content_base64": "not-base64",
    }

    with pytest.raises(ParserError) as exc:
        normalize_input("file", json.dumps(payload))

    assert exc.value.code == "invalid_base64"
