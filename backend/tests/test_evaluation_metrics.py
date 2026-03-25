import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.log_analyzer import analyze_log_lines
from backend.patterns import detect_patterns, identify_log_type

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLD_LOG_FILE = FIXTURES_DIR / "gold_logs_1000.log"
GOLD_LABEL_FILE = FIXTURES_DIR / "gold_labels_1000.json"


def _load_gold() -> tuple[str, dict]:
    text = GOLD_LOG_FILE.read_text(encoding="utf-8")
    labels = json.loads(GOLD_LABEL_FILE.read_text(encoding="utf-8"))
    return text, labels


def _to_key_set(findings: list[dict]) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    for finding in findings:
        finding_type = str(finding.get("type", ""))
        line = int(finding.get("line", 0))
        if finding_type and line > 0:
            keys.add((finding_type, line))
    return keys


def _compute_metrics(expected: set[tuple[str, int]], actual: set[tuple[str, int]]) -> dict[str, float | int]:
    tp = len(expected & actual)
    fp = len(actual - expected)
    fn = len(expected - actual)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
    }


def test_gold_dataset_line_count_is_stable() -> None:
    text, _ = _load_gold()
    assert len(text.splitlines()) == 1000


def test_gold_dataset_detection_quality_thresholds() -> None:
    text, labels = _load_gold()

    expected = {(item["type"], item["line"]) for item in labels["expected_findings"]}
    detected = detect_patterns(text)
    actual = _to_key_set(detected)

    metrics = _compute_metrics(expected, actual)
    thresholds = labels["thresholds"]

    assert metrics["precision"] >= thresholds["overall_precision_min"], metrics
    assert metrics["recall"] >= thresholds["overall_recall_min"], metrics
    assert metrics["fp"] <= thresholds["max_false_positives"], metrics


def test_gold_dataset_log_type_classification() -> None:
    text, labels = _load_gold()

    profile = identify_log_type(text)

    assert profile["log_type"] == labels["expected_log_type"]
    assert profile["log_sub_type"] == labels["expected_log_sub_type"]
    assert profile["confidence"] > 0


def test_gold_dataset_log_analyzer_summary() -> None:
    text, labels = _load_gold()
    expected = labels["expected_summary"]

    result = analyze_log_lines(text)

    assert result["line_count"] == expected["line_count"]
    assert result["summary"]["total_findings"] == expected["total_findings"]
    assert result["summary"]["unique_lines_affected"] == expected["unique_lines_affected"]
    assert result["grouped_findings"]["by_severity"] == expected["by_severity"]
