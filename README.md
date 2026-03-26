# LogGuard

AI Secure Data Intelligence Platform for log ingestion, detection, analysis, risk scoring, policy enforcement, and AI-assisted security insights.

## Current Status

Phase 1 core workflow is implemented:

- Multi-input normalization (text, file, sql, chat, log)
- Sensitive pattern detection with risk labels and redaction hints
- Line-aware log analysis with grouped findings and log-type classification
- Gemini-powered AI summary and chat responses with graceful fallback
- Risk scoring and policy application (masking + optional blocking)
- Frontend upload, chat, log viewer, and insights experience

## Architecture

Pipeline:

Input -> Parser -> Pattern Detection -> Log Analyzer -> Risk Engine -> Policy Engine -> AI Insights -> Response

Core backend modules:

- backend/parser.py
- backend/patterns.py
- backend/log_analyzer.py
- backend/risk_engine.py
- backend/policy_engine.py
- backend/ai_insights.py
- backend/main.py

Frontend app:

- frontend_v2/src/app

## API Endpoints

- GET /health
- POST /analyze
- POST /analyze/upload
- POST /chat

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

## Policy Behavior

- mask=true: sensitive matches are transformed in processed_content
- block_high_risk=true: high/critical results can return action=blocked
- Frontend now renders processed policy output (masked/blocked) in log display

## Important Note On Plan Alignment

The plan specifies Phase 1 as mask-and-warn (no blocking). Current code supports optional blocking behind block_high_risk. Keep block_high_risk=false to align strictly with that Phase 1 policy decision.
