# BookLeaf AI Support Automation Platform

BookLeaf is a full-stack AI support operations platform for publishing workflows.  
It combines conversational AI, identity resolution, intent routing, structured database retrieval, and optional knowledge-base guidance in one enterprise-style support console.

## Highlights

- Full-stack monorepo (`frontend` + `backend`)
- AI chat orchestration with confidence and escalation logic
- Identity unification (email/phone/name/social signals)
- Multilingual handling (English, Hindi, Hinglish normalization)
- Conversational fast paths (`SMALLTALK`, `CONVERSATIONAL_IDENTITY`)
- Workflow trace UI for operational transparency
- Analytics dashboard for support operations
- Render Blueprint deployment (`render.yaml`)

## Tech Stack

- Frontend: React + Vite + TailwindCSS
- Backend: FastAPI (Python)
- Database: PostgreSQL (SQLAlchemy)
- AI: Groq (`llama-3.3-70b-versatile`)

## Repository Structure

```text
leafy/
  frontend/
  backend/
    app/
      ai/
      db/
      identity/
      models/
      rag/
      routes/
      schemas/
      services/
      workflows/
      utils/
  render.yaml
  README.md
```

## Core Capabilities

- `/api/chat` orchestration pipeline:
1. Normalize query
2. Classify intent
3. Resolve identity
4. Route to DB and/or KB (as needed)
5. Generate response
6. Score confidence
7. Escalate when required
8. Log all operational metadata

- Intent categories include:
  - `BOOK_STATUS`
  - `ROYALTY`
  - `AUTHOR_COPY`
  - `ADDON_STATUS`
  - `DASHBOARD_ACCESS`
  - `GENERAL_POLICY`
  - `SMALLTALK`
  - `CONVERSATIONAL_IDENTITY`
  - `UNKNOWN`

- Frontend includes:
  - AI chat command center
  - Voice input (browser-native speech recognition)
  - Workflow trace panel
  - Admin analytics dashboard
  - Publishing Workspace external integration entry

## Local Development

## 1) Backend

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env` (example values):

```env
ENV=development
API_PREFIX=/api
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.3-70b-versatile
```

Run API:

```bash
uvicorn app.main:app --reload --port 8000
```

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Set frontend env (`frontend/.env`):

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Render Deployment (Blueprint)

This repo contains a Render Blueprint file: `render.yaml`.

It provisions:
- `bookleaf-postgres` (PostgreSQL)
- `bookleaf-backend` (FastAPI web service)
- `bookleaf-frontend` (static site)

### Deploy steps

1. Push this repository to GitHub.
2. In Render dashboard: **New + -> Blueprint**.
3. Select this repository.
4. Set secret env var `GROQ_API_KEY`.
5. Deploy.

### Auto-wired variables

- Backend `DATABASE_URL` from Render Postgres
- Backend `FRONTEND_ORIGIN` from frontend service URL
- Frontend `VITE_API_BASE_URL` from backend service URL

## Persistence Notes

- Backend operational data (queries, escalations, analytics context) persists in PostgreSQL.
- Frontend chat session history is persisted in browser `localStorage` to avoid clearing on refresh/tab close on the same device.

## Useful Endpoints

- `GET /api/health`
- `POST /api/chat`
- `POST /api/ai/classify`
- `POST /api/identity/resolve`
- `GET /api/analytics/overview`
- `GET /api/analytics/recent-queries`
- `GET /api/escalations`

## License

Proprietary/internal project (update as needed).

