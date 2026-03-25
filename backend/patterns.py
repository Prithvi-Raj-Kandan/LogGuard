import logging
import re
from typing import Any, Iterable


logger = logging.getLogger("logguard.workflow")


RISK_LEVELS: dict[str, str] = {
    "email": "low",
    "phone": "medium",
    "password": "critical",
    "private_key": "critical",
    "jwt": "high",
    "bearer_token": "high",
    "api_key": "high",
    "aws_access_key": "high",
    "connection_string": "critical",
    "stack_trace": "medium",
    "internal_ip": "medium",
    "hostname": "low",
}


PATTERN_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "email",
        "risk": RISK_LEVELS["email"],
        "confidence": 0.75,
        "redaction_hint": "mask_partial",
        "regex": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    },
    {
        "type": "phone",
        "risk": RISK_LEVELS["phone"],
        "confidence": 0.65,
        "redaction_hint": "mask_all_but_last4",
        "regex": re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}\b"),
    },
    {
        "type": "password",
        "risk": RISK_LEVELS["password"],
        "confidence": 0.95,
        "redaction_hint": "mask_all",
        "regex": re.compile(
            r"(?i)\b(?:password|passwd|pwd|passphrase)\s*[:=]\s*['\"]?([^\s'\";,]+)['\"]?"
        ),
    },
    {
        "type": "private_key",
        "risk": RISK_LEVELS["private_key"],
        "confidence": 1.0,
        "redaction_hint": "mask_all",
        "regex": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    },
    {
        "type": "jwt",
        "risk": RISK_LEVELS["jwt"],
        "confidence": 0.85,
        "redaction_hint": "mask_all",
        "regex": re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    },
    {
        "type": "bearer_token",
        "risk": RISK_LEVELS["bearer_token"],
        "confidence": 0.9,
        "redaction_hint": "mask_all",
        "regex": re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~+\-/=]{12,}"),
    },
    {
        "type": "api_key",
        "risk": RISK_LEVELS["api_key"],
        "confidence": 0.88,
        "redaction_hint": "mask_all",
        "regex": re.compile(
            r"(?i)\b(?:api[_-]?key|x-api-key|client[_-]?secret)\b\s*[:=]\s*['\"]?([A-Za-z0-9._\-]{8,})['\"]?"
        ),
    },
    {
        "type": "aws_access_key",
        "risk": RISK_LEVELS["aws_access_key"],
        "confidence": 0.92,
        "redaction_hint": "mask_all",
        "regex": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    },
    {
        "type": "connection_string",
        "risk": RISK_LEVELS["connection_string"],
        "confidence": 0.95,
        "redaction_hint": "mask_credentials",
        "regex": re.compile(
            r"(?i)\b(?:postgres|mysql|mongodb|redis)://[^\s:@]+:[^\s@]+@[^\s]+"
        ),
    },
    {
        "type": "stack_trace",
        "risk": RISK_LEVELS["stack_trace"],
        "confidence": 0.7,
        "redaction_hint": "none",
        "regex": re.compile(r"(?i)(Traceback \(most recent call last\)|Exception in thread|at\s+\S+\.\S+\(\S+\.java:\d+\))"),
    },
    {
        "type": "internal_ip",
        "risk": RISK_LEVELS["internal_ip"],
        "confidence": 0.7,
        "redaction_hint": "mask_partial",
        "regex": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    },
    {
        "type": "hostname",
        "risk": RISK_LEVELS["hostname"],
        "confidence": 0.55,
        "redaction_hint": "none",
        "regex": re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+(?:internal|local|corp|lan)\b"),
    },
]


LOG_TYPE_RULES: list[dict[str, Any]] = [
    {
        "log_type": "web_server_access",
        "log_sub_type": "nginx_apache_access",
        "patterns": [
            re.compile(r'"(?:GET|POST|PUT|DELETE|PATCH|OPTIONS)\s+[^\"]+\s+HTTP/\d\.\d"'),
            re.compile(r"\b\d{3}\s+\d+\b"),
            re.compile(r"\b(?:nginx|apache|httpd)\b", re.IGNORECASE),
        ],
    },
    {
        "log_type": "linux_syslog",
        "log_sub_type": "system_auth_kernel",
        "patterns": [
            re.compile(r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}", re.IGNORECASE),
            re.compile(r"\b(?:systemd|sshd|sudo|kernel)\b", re.IGNORECASE),
        ],
    },
    {
        "log_type": "application_structured_json",
        "log_sub_type": "json_lines",
        "patterns": [
            re.compile(r'^\s*\{.*"(?:level|timestamp|message|msg)".*\}\s*$'),
        ],
    },
    {
        "log_type": "web_server_error",
        "log_sub_type": "http_error_trace",
        "patterns": [
            re.compile(r"\b(?:ERROR|WARN|CRITICAL|FATAL)\b"),
            re.compile(r"\b(?:stack trace|exception|traceback)\b", re.IGNORECASE),
        ],
    },
    {
        "log_type": "database",
        "log_sub_type": "sql_nosql_engine",
        "patterns": [
            re.compile(r"\b(?:postgres|mysql|mongodb|redis|sqlstate|query)\b", re.IGNORECASE),
        ],
    },
    {
        "log_type": "container_kubernetes",
        "log_sub_type": "container_runtime_or_k8s",
        "patterns": [
            re.compile(r"\b(?:kubelet|kubectl|pod|containerd|docker)\b", re.IGNORECASE),
        ],
    },
]


def _scan_patterns(lines: Iterable[tuple[int, str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    per_type_counts: dict[str, int] = {}

    for line_number, line_text in lines:
        for definition in PATTERN_DEFINITIONS:
            for match in definition["regex"].finditer(line_text):
                # Ignore very short generic values that cause common token false positives.
                matched_value = match.group(0)
                if definition["type"] in {"api_key", "bearer_token"} and len(matched_value) < 14:
                    continue

                findings.append(
                    {
                        "type": definition["type"],
                        "value": matched_value,
                        "risk": definition["risk"],
                        "confidence": definition["confidence"],
                        "redaction_hint": definition["redaction_hint"],
                        "line": line_number,
                    }
                )
                pattern_type = str(definition["type"])
                per_type_counts[pattern_type] = per_type_counts.get(pattern_type, 0) + 1

    logger.info(
        "workflow=patterns step=scan_completed findings=%d distinct_types=%d counts=%s",
        len(findings),
        len(per_type_counts),
        per_type_counts,
    )

    return findings


def detect_patterns(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines() or [text]
    logger.info("workflow=patterns step=detect_patterns_started line_count=%d", len(lines))
    indexed = [(index + 1, line) for index, line in enumerate(lines)]
    findings = _scan_patterns(indexed)
    logger.info("workflow=patterns step=detect_patterns_completed findings=%d", len(findings))
    return findings


def detect_patterns_in_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    logger.info("workflow=patterns step=detect_patterns_in_lines_started line_count=%d", len(lines))
    indexed = [
        (int(line.get("line_number", index + 1)), str(line.get("text", "")))
        for index, line in enumerate(lines)
    ]
    findings = _scan_patterns(indexed)
    logger.info("workflow=patterns step=detect_patterns_in_lines_completed findings=%d", len(findings))
    return findings


def identify_log_type(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    logger.info("workflow=patterns step=identify_log_type_started line_count=%d", len(lines))
    if not lines:
        logger.info("workflow=patterns step=identify_log_type_completed log_type=unknown confidence=0.00")
        return {
            "log_type": "unknown",
            "log_sub_type": "unknown",
            "confidence": 0.0,
            "evidence_lines": [],
        }

    best_type = "unknown"
    best_sub_type = "unknown"
    best_score = 0
    evidence_lines: list[int] = []

    for rule in LOG_TYPE_RULES:
        score = 0
        local_evidence: list[int] = []
        for index, line in enumerate(lines, start=1):
            for pattern in rule["patterns"]:
                if pattern.search(line):
                    score += 1
                    if len(local_evidence) < 5:
                        local_evidence.append(index)
                    break

        if score > best_score:
            best_score = score
            best_type = rule["log_type"]
            best_sub_type = rule.get("log_sub_type", "unknown")
            evidence_lines = local_evidence

    confidence = round(min(1.0, best_score / max(1, len(lines) * 0.2)), 2)
    if best_score == 0:
        logger.info("workflow=patterns step=identify_log_type_completed log_type=unknown confidence=0.00")
        return {
            "log_type": "unknown",
            "log_sub_type": "unknown",
            "confidence": 0.0,
            "evidence_lines": [],
        }

    logger.info(
        "workflow=patterns step=identify_log_type_completed log_type=%s log_sub_type=%s confidence=%.2f",
        best_type,
        best_sub_type,
        confidence,
    )
    return {
        "log_type": best_type,
        "log_sub_type": best_sub_type,
        "confidence": confidence,
        "evidence_lines": evidence_lines,
    }
