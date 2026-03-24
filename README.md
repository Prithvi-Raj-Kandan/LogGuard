# LogGuard
AI secure data intelligence platform

## LG-101 Scaffold Status

This repository now includes the LG-101 project skeleton:

- Backend module stubs for parser, patterns, log analyzer, AI insights, risk engine, and policy engine
- FastAPI app with `GET /health` and placeholder `POST /analyze`
- Frontend React scaffold with `App.jsx` and required components

## Run Backend

From the project root:

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

## Run Frontend

From `frontend`:

```bash
npm install
npm run dev
```

## Environment Setup

Copy `.env.example` to `.env` and fill keys as needed:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `VITE_API_BASE_URL`
