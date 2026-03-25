import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.patterns import detect_patterns, detect_patterns_in_lines, identify_log_type


def test_detect_patterns_finds_sensitive_values() -> None:
    text = """
user_email=admin@company.com
password=supersecret
Authorization: Bearer abcdefghijklmnopqrstuvwxyz
api_key=sk-prod-1234567890
Traceback (most recent call last):
""".strip()

    findings = detect_patterns(text)
    finding_types = {item["type"] for item in findings}

    assert "email" in finding_types
    assert "password" in finding_types
    assert "bearer_token" in finding_types
    assert "api_key" in finding_types
    assert "stack_trace" in finding_types


def test_detect_patterns_in_lines_includes_line_number() -> None:
    lines = [
        {"line_number": 1, "text": "INFO ok"},
        {"line_number": 2, "text": "password=admin123"},
    ]

    findings = detect_patterns_in_lines(lines)

    assert findings
    assert findings[0]["line"] == 2


def test_identify_log_type_web_access() -> None:
    text = """
127.0.0.1 - - [25/Mar/2026:10:00:01 +0000] \"GET /index.html HTTP/1.1\" 200 532
127.0.0.1 - - [25/Mar/2026:10:00:02 +0000] \"POST /login HTTP/1.1\" 401 120
""".strip()

    profile = identify_log_type(text)

    assert profile["log_type"] == "web_server_access"
    assert profile["log_sub_type"] == "nginx_apache_access"
    assert profile["confidence"] > 0


def test_identify_log_type_linux_syslog() -> None:
    text = """
Mar 25 12:00:01 prod-vm sshd[123]: Failed password for invalid user root from 10.0.0.4 port 49822 ssh2
Mar 25 12:00:04 prod-vm sudo[220]: pam_unix(sudo:auth): authentication failure
""".strip()

    profile = identify_log_type(text)

    assert profile["log_type"] == "linux_syslog"
    assert profile["log_sub_type"] == "system_auth_kernel"
