# LogGuard

AI Secure Data Intelligence Platform for log ingestion, detection, analysis, risk scoring, policy enforcement, and AI-assisted security insights.

LogGuard helps teams inspect logs and other text-like inputs for sensitive data exposure and security risks.
It combines deterministic pattern detection with AI-generated summaries so users can quickly understand what was found and what to do next. 
The platform provides a chat interface for the user to interact and make queries with respect to the log files.
Link: https://log-guard-silk.vercel.app/

## Features

- Multi-input parsing and normalization for text, logs, files, SQL, and chat payloads
- Security pattern detection with line-aware findings, confidence, risk labels, and redaction hints
- Log analysis pipeline with type classification, grouped findings, and severity summaries
- Risk and policy enforcement with weighted scoring, masking, warnings, and optional blocking mode
- AI-assisted analysis using Gemini for contextual summary and follow-up chat responses
- End-to-end web experience with upload, log viewer, chat interface, severity-grouped warnings, and insights panels

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

