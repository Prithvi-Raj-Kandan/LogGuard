# LogGuard Implementation Plan

## Scope and Ticketing Model

- Phase 1 focuses on core responsibilities and mandatory judging criteria.
- Phase 1 ticket range: LG-101 to LG-10x.
- Phase 2 focuses on advanced challenges and bonus features.
- Phase 2 ticket range: LG-201 to LG-20x.

## Execution Principles

- Keep each important capability in a separate ticket.
- Keep response contracts stable early to avoid integration churn.
- Build test fixtures in parallel with each module, not at the end.
- For every executed ticket, update LG-110 evaluation artifacts in parallel.
- Use feature flags for advanced or risky behavior.

## Global Workflow

1. Implement Phase 1 tickets in dependency order.
2. Run Phase 1 quality gate and demo checks.
3. Start Phase 2 only after Phase 1 sign-off.
4. Run final benchmark and showcase packaging.

## Phase 1: Core Responsibilities

### LG-101: Project Bootstrap and Architecture Skeleton

Description:
- Initialize backend and frontend skeleton from the target project structure.
- Define baseline interfaces and shared contracts for all modules.

Files to create:
- backend/main.py
- backend/parser.py
- backend/patterns.py
- backend/log_analyzer.py
- backend/ai_insights.py
- backend/risk_engine.py
- backend/policy_engine.py
- frontend/App.jsx
- frontend/components/FileUpload.jsx
- frontend/components/LogViewer.jsx
- frontend/components/InsightsPanel.jsx
- plan.md

Execution steps:
1. Create all required directories and files.
2. Add placeholder function signatures and module boundaries.
3. Define input and output schema shapes as shared contracts.
4. Add local run instructions for backend and frontend.

Done when:
- All modules exist and import correctly.
- Backend and frontend both start locally.
- Contract stubs are documented and agreed.

Critical points:
- Do not hardcode API keys or secrets.
- Keep interfaces minimal and extensible.

Tests:
- Backend startup smoke test.
- Frontend startup smoke test.

Workflow and dependencies:
- Blocks all downstream tickets.

---

### LG-102: Input Parser and Normalization

Description:
- Support text, file, sql, chat, and log inputs.
- Include full PDF and DOC extraction in Phase 1.

Files to create or update:
- backend/parser.py
- optional extraction helpers module(s)

Execution steps:
1. Build parser adapters per input type.
2. Implement PDF and DOC extraction path.
3. Normalize all outputs into one internal data format.
4. Preserve optional line mapping metadata for logs.
5. Add deterministic parse-error categories.

Done when:
- Each required input type returns valid normalized payload.
- Parse failures return predictable error shape.

Critical points:
- Preserve content fidelity for downstream detection.
- Guard memory usage for large files.

Tests:
- Fixture tests per input type.
- Corrupt and unsupported file tests.
- Large-file parser stability tests.

Workflow and dependencies:
- Depends on LG-101.
- Required by LG-103, LG-104, LG-107.

---

### LG-103: Detection Patterns and Risk Mapping

Description:
- Build the regex detection layer and risk labels.
- Detect emails, phone numbers, passwords, tokens, API keys, and stack traces.

Files to create or update:
- backend/patterns.py

Execution steps:
1. Add regex patterns for required sensitive entities.
2. Map each finding type to default risk level and weight.
3. Standardize finding output object shape.
4. Add redaction hints per finding type.

Done when:
- Pattern engine returns consistent findings across inputs.
- Risk labels are deterministic.

Critical points:
- Balance precision and recall to reduce false positives.
- Keep patterns extensible for LG-202.

Tests:
- True-positive fixture set.
- False-positive control fixture set.
- Regression fixtures for pattern updates.

Workflow and dependencies:
- Depends on LG-102.
- Feeds LG-104, LG-106, LG-107.

---

### LG-104: Log Analyzer Module

Description:
- Build line-by-line log analysis with line references and grouped findings.

Files to create or update:
- backend/log_analyzer.py

Execution steps:
1. Parse normalized log content line-by-line.
2. Apply detection patterns to each line.
3. Attach line number and evidence snippet to findings.
4. Produce grouped summary stats by finding type and severity.

Done when:
- Analyzer returns deterministic line-aware findings.
- Summary counters match fixture expectations.

Critical points:
- Preserve line numbers through chunking boundaries.
- Avoid expensive repeated scans.

Tests:
- Multi-line fixtures.
- Boundary tests for first and last lines.
- Mixed-severity aggregation tests.

Workflow and dependencies:
- Depends on LG-102 and LG-103.

---

### LG-105: AI Insights Integration (Gemini)

Description:
- Generate meaningful security insights from findings and log context.

Files to create or update:
- backend/ai_insights.py

Execution steps:
1. Define strict prompt and response schema.
2. Integrate Gemini client with timeout and retry.
3. Validate model output before including in API response.
4. Add fallback non-AI summary if model call fails.

Done when:
- Insights are actionable and non-generic.
- Endpoint continues to work when Gemini is unavailable.

Critical points:
- Minimize sensitive content sent to model.
- Keep model id and keys configurable via environment variables.

Tests:
- Mocked Gemini response schema tests.
- Timeout and exception fallback tests.

Workflow and dependencies:
- Depends on LG-103 and LG-104.

---

### LG-106: Risk Engine and Policy Engine

Description:
- Compute risk score and level, then apply masking policy.
- Phase 1 policy behavior: mask and warn only, never block.

Files to create or update:
- backend/risk_engine.py
- backend/policy_engine.py

Execution steps:
1. Define weighted scoring and threshold bands.
2. Implement classification output (score plus level).
3. Implement masking transformation for sensitive findings.
4. Emit warning action metadata without blocking requests.

Done when:
- Risk output is stable and deterministic.
- Masking works with line-aware findings.

Critical points:
- Keep scoring transparent and reproducible.
- Preserve readability after masking.

Tests:
- Threshold boundary tests.
- Mask transformation tests.
- Mixed finding-set scoring tests.

Workflow and dependencies:
- Depends on LG-103 and LG-104.

---

### LG-107: FastAPI Analyze Endpoint Orchestration

Description:
- Wire parser, detector, log analyzer, AI insights, risk, and policy into one endpoint.

Files to create or update:
- backend/main.py

Execution steps:
1. Implement POST /analyze request handling.
2. Orchestrate full pipeline in fixed order.
3. Return contract-compliant success response.
4. Return deterministic error payload for failures.
5. Support options such as mask and log_analysis.

Done when:
- Endpoint contract matches project spec.
- All major paths return valid response shape.

Critical points:
- Keep request and response schema versioned.
- Avoid leaking internal stack traces.

Tests:
- API integration tests by input_type.
- Error-path tests with malformed payloads.

Workflow and dependencies:
- Depends on LG-102, LG-103, LG-104, LG-105, LG-106.

---

### LG-108: Frontend Baseline Integration

Description:
- Deliver initial UI flow for upload/input, findings display, and insights panel.

Files to create or update:
- frontend/App.jsx
- frontend/components/FileUpload.jsx
- frontend/components/InsightsPanel.jsx
- optional initial usage of frontend/components/LogViewer.jsx

Execution steps:
1. Build input UI for supported submission types.
2. Integrate API call to analyze endpoint.
3. Render summary, findings, risk score, risk level, and insights.
4. Add loading, empty, and error states.

Done when:
- End-to-end submission and result rendering works.

Critical points:
- Keep frontend strictly aligned to backend response contract.
- Handle partial failures gracefully.

Tests:
- Component behavior tests.
- End-to-end happy path tests.

Workflow and dependencies:
- Depends on LG-107.

---

### LG-109: Reliability and Guardrails

Description:
- Harden system behavior for invalid payloads, oversized files, and timeout scenarios.

Files to create or update:
- backend/main.py
- backend/parser.py
- frontend/App.jsx

Execution steps:
1. Add payload size limits and validation checks.
2. Add timeout policies and safe retries where appropriate.
3. Standardize safe client-facing error messages.
4. Add explicit observability hooks for major failure types.

Done when:
- Negative paths are predictable and non-breaking.
- System degrades gracefully under stress.

Critical points:
- No stack traces in client output.
- No ambiguous error messages.

Tests:
- Oversized input tests.
- Timeout simulation tests.
- Invalid schema tests.

Workflow and dependencies:
- Runs alongside LG-108 polish.
- Must complete before LG-10x.

---

### LG-110: Evaluation Framework

Description:
- Build a measurable evaluation pipeline to verify pattern detection quality and prevent regressions.

Files to create or update:
- backend/tests/test_patterns.py
- backend/tests/fixtures/
- backend/tests/test_evaluation_metrics.py
- backend/patterns.py

Execution steps:
1. Build fixture sets for true positives, false positives, and mixed realistic logs.
2. Define expected labels per fixture: pattern type, line number, and risk level.
3. Implement evaluation helpers to compute precision, recall, false positives, and false negatives per pattern.
4. Add threshold assertions for critical and high-risk pattern quality.
5. Add line-number accuracy checks for labeled fixtures.
6. Integrate the evaluation suite into the default backend test run.

Done when:
- Detection quality metrics are computed automatically and validated against thresholds.
- Any regression in pattern quality fails tests.

Critical points:
- Include web-access-log fixtures to control phone/token false positives.
- Keep fixtures versioned and deterministic so quality trends remain comparable.

Tests:
- Per-pattern precision/recall tests.
- False-positive control tests on benign access logs.
- Labeled line-number accuracy tests.

Workflow and dependencies:
- Depends on LG-103.
- Runs in parallel with LG-104 and LG-106.
- Must complete before LG-10x.

---

### LG-10x: Phase 1 Quality Gate and Demo Readiness

Description:
- Validate all mandatory criteria and prepare final Phase 1 demo flow.

Files to create or update:
- test fixtures and report artifacts
- demo script document

Execution steps:
1. Execute matrix across all input types and major risk patterns.
2. Verify masking and score consistency.
3. Validate response examples against project expectations.
4. Document known limitations for Phase 2 carryover.

Done when:
- Phase 1 acceptance checklist is complete and signed off.

Critical points:
- Prioritize log analysis scenarios due to evaluation weight.

Tests:
- End-to-end regression suite.
- Repeatability check for risk scoring.

Workflow and dependencies:
- Depends on LG-101 through LG-110.

## Phase 2: Advanced Challenges

### LG-201: Advanced Log Viewer

Description:
- Upgrade log visualization with line numbers, highlights, and risk markers.

Files to create or update:
- frontend/components/LogViewer.jsx
- frontend/App.jsx

Execution steps:
1. Render logs with line-number gutter.
2. Highlight sensitive lines by severity.
3. Add filter controls by risk type.

Done when:
- User can quickly inspect risky lines visually.

Critical points:
- Keep rendering performant for large logs.

Tests:
- UI rendering and filter behavior tests.

Workflow and dependencies:
- Starts after LG-10x.

---

### LG-202: Advanced Security Heuristics

Description:
- Detect repeated failures, suspicious IP behavior, and brute-force indicators.

Files to create or update:
- backend/log_analyzer.py
- backend/patterns.py

Execution steps:
1. Add counters and window-based heuristics.
2. Detect suspicious source concentration and repeated auth failures.
3. Attach confidence and evidence to heuristic findings.

Done when:
- Heuristic findings appear with clear context and confidence.

Critical points:
- Reduce noisy detections in normal traffic patterns.

Tests:
- Scenario fixtures for repeated failures and IP bursts.

Workflow and dependencies:
- Depends on LG-201 baseline integration expectations and Phase 1 analyzer stability.

---

### LG-203: Large-Log Chunking and Performance

Description:
- Optimize parser and analyzer for high-volume log files.

Files to create or update:
- backend/parser.py
- backend/log_analyzer.py

Execution steps:
1. Implement chunked ingestion strategy.
2. Preserve finding continuity across chunk boundaries.
3. Measure and tune latency and memory use.

Done when:
- Large-log performance improves with accuracy preserved.

Critical points:
- No finding loss at chunk transitions.

Tests:
- Performance benchmarks.
- Large-file accuracy regression tests.

Workflow and dependencies:
- Depends on LG-202.

---

### LG-204: Optional Streaming Analysis Mode

Description:
- Add feature-flagged near-real-time analysis mode for log streams.

Files to create or update:
- backend/main.py
- backend/log_analyzer.py
- optional frontend stream status UI

Execution steps:
1. Add streaming ingestion endpoint or mode.
2. Emit progressive analysis snapshots.
3. Protect with feature flag and fallback to batch mode.

Done when:
- Stream mode works without destabilizing batch mode.

Critical points:
- Backpressure and timeout controls are required.

Tests:
- Stream lifecycle tests.
- Recovery and reconnect tests.

Workflow and dependencies:
- Depends on LG-203.

---

### LG-205: Cross-Log Correlation

Description:
- Correlate patterns and anomalies across multiple logs/uploads.

Files to create or update:
- backend/log_analyzer.py
- backend/risk_engine.py

Execution steps:
1. Create correlation keys and event linking logic.
2. Build summary view of linked suspicious chains.
3. Feed correlated evidence into risk scoring.

Done when:
- Related findings across files are summarized clearly.

Critical points:
- Correlation logic must be explainable.

Tests:
- Multi-file correlation fixtures.

Workflow and dependencies:
- Depends on LG-204.

---

### LG-206: Rate Limiting and Abuse Safeguards

Description:
- Protect service from overload and misuse.

Files to create or update:
- backend/main.py
- backend/policy_engine.py

Execution steps:
1. Add request throttling and quotas.
2. Define client-safe responses for rate-limited requests.
3. Add telemetry for abuse patterns.

Done when:
- Overload and abusive usage are controlled.

Critical points:
- Keep legitimate usage unblocked where possible.

Tests:
- Concurrent load and throttling tests.

Workflow and dependencies:
- Depends on LG-204 and LG-205.

---

### LG-207: Observability and Diagnostics

Description:
- Add per-stage timing, failure counters, and structured diagnostics.

Files to create or update:
- backend/main.py
- backend/parser.py
- backend/log_analyzer.py
- backend/ai_insights.py

Execution steps:
1. Add stage-level timing metrics.
2. Add structured logs with correlation ids.
3. Add operational counters for failures and retries.

Done when:
- Operators can identify bottlenecks and failure hotspots quickly.

Critical points:
- Avoid logging sensitive raw data.

Tests:
- Telemetry presence tests.
- Alert threshold simulation tests.

Workflow and dependencies:
- Depends on LG-206.

---

### LG-20x: Phase 2 Final Benchmark and Showcase

Description:
- Validate advanced capability targets and prepare final showcase package.

Files to create or update:
- benchmark report and demo script artifacts

Execution steps:
1. Run full Phase 2 regression and benchmarks.
2. Compare baseline and optimized performance.
3. Package final demo scenarios and narrative.

Done when:
- Advanced acceptance checklist is complete.
- Demo package is ready for judging.

Critical points:
- Ensure all optional features can be toggled cleanly.

Tests:
- Full advanced regression suite.
- Benchmark replay consistency checks.

Workflow and dependencies:
- Depends on LG-201 through LG-207.

## Ticket Dependency Summary

1. LG-101 blocks all work.
2. LG-102 unlocks LG-103 and LG-104.
3. LG-103 plus LG-104 unlock LG-105 and LG-106.
4. LG-102 plus LG-103 plus LG-104 plus LG-105 plus LG-106 unlock LG-107.
5. LG-107 unlocks LG-108.
6. LG-108, LG-109, and LG-110 must complete before LG-10x.
7. LG-10x gates all LG-20x series work.

## Quality Gates

Phase 1 gate:
- Mandatory input types supported.
- Core detections validated.
- Risk and masking deterministic.
- Frontend baseline complete.

Phase 2 gate:
- Advanced heuristics validated.
- Performance improvements measured.
- Streaming and correlation validated if enabled.
- Observability and abuse controls operational.

## Project Decisions Locked

- AI provider: Gemini.
- PDF and DOC support: included in Phase 1.
- Policy behavior in Phase 1: mask and warn only, no blocking.
- Advanced visual and challenge features: Phase 2 scope.
