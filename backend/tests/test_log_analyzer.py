import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.log_analyzer import analyze_log_lines


def test_analyze_log_lines_includes_line_number_and_evidence() -> None:
    text = """
INFO startup complete
user_email=admin@company.com
password=supersecret123
""".strip()

    result = analyze_log_lines(text)

    assert result["line_count"] == 3
    assert result["findings"]

    password_finding = next(item for item in result["findings"] if item["type"] == "password")
    assert password_finding["line"] == 3
    assert "password=supersecret123" in password_finding["evidence_snippet"]


def test_analyze_log_lines_handles_first_and_last_line_boundaries() -> None:
    text = """
email=first@company.com
INFO middle
-----BEGIN PRIVATE KEY-----
""".strip()

    result = analyze_log_lines(text)

    key_set = {(item["type"], item["line"]) for item in result["findings"]}

    assert ("email", 1) in key_set
    assert ("private_key", 3) in key_set


def test_analyze_log_lines_grouped_summary_mixed_severities() -> None:
    text = """
password=admin123
api_key=sk-prod-1234567890
internal_ip=10.1.2.3
email=info@company.com
""".strip()

    result = analyze_log_lines(text)
    grouped = result["grouped_findings"]
    by_severity = grouped["by_severity"]

    assert result["summary"]["total_findings"] == 5
    assert result["summary"]["unique_lines_affected"] == 4
    assert by_severity["critical"] == 1
    assert by_severity["high"] == 1
    assert by_severity["medium"] == 2
    assert by_severity["low"] == 1

    assert grouped["by_type"]["password"]["count"] == 1
    assert grouped["by_type"]["password"]["lines"] == [1]
