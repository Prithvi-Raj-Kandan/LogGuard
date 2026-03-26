# LogGuard

AI Secure Data Intelligence Platform for log ingestion, detection, analysis, risk scoring, policy enforcement, and AI-assisted security insights.

## Features

- Multi-input ingestion and normalization for text, file, sql, chat, and log payloads
- File parsing support for txt, log, pdf, docx, and legacy doc fallback extraction
- Structured parser metadata including line counts, chunk counts, extraction method, and warnings
- Regex-based sensitive data detection with line references and confidence values
- Detection coverage for emails, phone numbers, passwords, API keys, bearer tokens, JWTs, private keys, AWS keys, connection strings, stack traces, internal IPs, and hostnames
- Deterministic risk labels and redaction hints per detected pattern
- Log-type classification (web access, web error, linux syslog, application JSON, database, container/kubernetes)
- Line-by-line log analyzer with evidence snippets and grouped summaries by type and severity
- Weighted risk scoring engine with risk level classification and severity breakdown
- Policy engine for masking sensitive values using redaction rules
- Optional high-risk blocking action when policy mode enables block_high_risk
- AI summary generation using Gemini based on analyzer context and metadata
- AI chat assistant endpoint using report context plus recent chat history
- Interactive log viewer with severity-aware highlighting support
- Unified Security Warnings panel grouped by severity with expandable sections
- AI Summary panel 
- Frontend handling of policy-processed content so masked/blocked output is reflected in displayed logs

## Architecture

Pipeline:

Input -> Parser -> Pattern Detection -> Log Analyzer -> Risk Engine -> Policy Engine -> AI Insights -> Response

## Environment Setup

Create a root .env file (or backend/.env), based on .env.example:

- GEMINI_API_KEY=your_key
- GEMINI_MODEL=gemini-1.5-flash
- VITE_API_BASE_URL=http://localhost:8000

Notes:

- If GEMINI_API_KEY is missing, AI summary/chat fall back safely.
- Frontend reads VITE_API_BASE_URL from frontend_v2/.env or Vite environment.

## Run Backend

From project root:

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

## Run Frontend

From frontend_v2:

```bash
npm install
npm run dev
```

Production build:

```bash
npm run build
```

## Testing

From backend/tests:

```bash
python -m pytest -q
```

Targeted evaluation suite:

```bash
python -m pytest test_evaluation_metrics.py test_patterns.py test_parser.py -q
```

