import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_insights import generate_insights


def _sample_context() -> dict:
    return {
        "request_id": "req-123",
        "content_type": "logs",
        "line_count": 20,
        "findings": [
            {"type": "password", "risk": "critical", "line": 4},
            {"type": "api_key", "risk": "high", "line": 8},
        ],
        "log_profile": {
            "log_type": "web_server_access",
            "log_sub_type": "nginx_apache_access",
            "confidence": 0.82,
        },
        "grouped_findings": {
            "by_severity": {"critical": 1, "high": 1, "medium": 0, "low": 0}
        },
    }


def test_generate_insights_fallback_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    insights = generate_insights(_sample_context())

    assert len(insights) == 1
    assert "GEMINI_API_KEY" in insights[0]


def test_generate_insights_uses_model_when_available(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    def fake_call(prompt: str, api_key: str, model_name: str, timeout_seconds: float) -> str:
        assert "logguard security assistant" in prompt.lower()
        assert api_key == "dummy-key"
        assert model_name == "gemini-test-model"
        assert timeout_seconds > 0
        return "Rotate exposed credentials immediately. Restrict access to log exports."

    monkeypatch.setattr("backend.ai_insights._call_gemini", fake_call)

    insights = generate_insights(_sample_context())

    assert len(insights) == 1
    assert insights[0].startswith("Rotate exposed credentials immediately")


def test_generate_insights_falls_back_on_model_error(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")

    def raising_call(*_args, **_kwargs):
        raise RuntimeError("provider_down")

    monkeypatch.setattr("backend.ai_insights._call_gemini", raising_call)

    insights = generate_insights(_sample_context())

    assert len(insights) == 1
    assert "model call failed" in insights[0].lower()