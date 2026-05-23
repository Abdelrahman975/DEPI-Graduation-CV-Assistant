# CV Assistant RAG

Local FastAPI project for CV parsing, ATS-style scoring, interview preparation, job recommendation, and CV chat.

## Data Sources

The project reads local files from:

- `data\clean_jobs.csv`
- `data\new\coding_interview_question_bank.csv`
- `data\resume-ats-score-v1-en\train.csv`
- `data\resume-ats-score-v1-en\validation.csv`
- `data\new\AI_Resume_Screening.csv`

## Setup

```powershell
cd E:\DEPI-study\DEPI-graduation-project\g_project_cv_g
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Gemini key to `.env`:

```env
GOOGLE_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash-lite
SESSION_BACKEND=auto
CONN_STR=postgresql://postgres:postgres@localhost:5432/rag_test_db
```

`SESSION_BACKEND=auto` uses PostgreSQL for users, chats, and message history when
`CONN_STR` is reachable. If PostgreSQL is unavailable, the app falls back to JSON
files under `storage\sessions` so the UI and API still work.

## Build Local Index

```powershell
python .\scripts\build_index.py
```

This command rebuilds `storage\chroma` from the local CSV files. If an older Chroma
index exists, it is removed first to avoid version/metadata conflicts.

If Chroma or the embedding model is unavailable, the app still runs with lexical fallback search.

## Run

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- UI: `http://localhost:8000/app`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Main Endpoints

- `POST /api/v1/users`
- `POST /api/v1/chats`
- `GET /api/v1/users/{user_id}/chats`
- `GET /api/v1/chats/{session_id}`
- `DELETE /api/v1/chats/{session_id}`
- `POST /api/v1/cv/analyze`
- `POST /api/v1/chat/message`
- `POST /api/v1/chat/stream`
- `GET /api/v1/jobs/recommendations/{session_id}`
- `POST /api/v1/interview/questions`
- `POST /api/v1/index/rebuild`
