# ResearchHub AI

**Intelligent Research Paper Management and Analysis System using Agentic AI**

> Discover, import, organise, and converse with academic papers using Groq Llama 3.3, pgvector, and Retrieval-Augmented Generation.



Demo Video Link:
[Research Hub AI](URLhttps://drive.google.com/drive/folders/1dtP_hYTk2EhyX53hVI8JPOODynaniFVu)

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│  React + TypeScript Frontend  (port 3000)                      │
│   Login · Search Papers · Workspaces · AI Chatbot              │
└───────────────────────┬────────────────────────────────────────┘
                        │ HTTP / REST
┌───────────────────────▼────────────────────────────────────────┐
│  FastAPI Backend  (port 8000)                                  │
│   /auth  /papers  /workspaces  /chat                           │
└───┬────────────────────┬───────────────────────┬───────────────┘
    │                    │                       │
    ▼                    ▼                       ▼
PostgreSQL          pgvector                Groq API
(ResearchHub DB)    similarity search       Llama-3.3-70b
port 5432           (768-dim embeddings)    temperature 0.3
```

---

## Tech Stack

| Layer         | Technology                                            |
| ------------- | ----------------------------------------------------- |
| Frontend      | React 18 + TypeScript + Tailwind CSS                  |
| Backend       | FastAPI + Uvicorn                                     |
| AI / LLM      | Groq —`llama-3.3-70b-versatile`                    |
| Embeddings    | Sentence Transformers `all-mpnet-base-v2` (768 dim) |
| Database      | PostgreSQL 16 (pgvector extension)                    |
| ORM           | SQLAlchemy 2                                          |
| Migrations    | Alembic                                               |
| Auth          | Passlib bcrypt + python-jose JWT                      |
| External APIs | arXiv API · PubMed E-utilities                       |
| Container     | Docker + Docker Compose                               |

---

## Project Structure

```
researchhub-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── database/
│   │   │   ├── database.py          # SQLAlchemy engine, session, init_db()
│   │   │   ├── models.py            # ORM models (User, Workspace, Paper, …)
│   │   │   └── schemas.py           # Pydantic request / response schemas
│   │   ├── routers/
│   │   │   ├── auth_router.py       # POST /auth/register, /login  GET /auth/me
│   │   │   ├── papers_router.py     # GET /papers/search  POST /papers/import
│   │   │   ├── workspace_router.py  # CRUD /workspaces + notes
│   │   │   └── chat_router.py       # POST /chat/query  GET /chat/messages
│   │   ├── services/
│   │   │   ├── search_service.py    # arXiv + PubMed unified search
│   │   │   ├── embedding_service.py # Sentence Transformer singleton
│   │   │   ├── vector_service.py    # pgvector cosine similarity search
│   │   │   ├── llm_service.py       # Groq Llama 3.3 inference
│   │   │   └── paper_service.py     # Import, workspace assignment, chunking
│   │   ├── agents/
│   │   │   └── research_agent.py    # RAG orchestration agent
│   │   ├── utils/
│   │   │   ├── auth_utils.py        # JWT + bcrypt helpers
│   │   │   ├── pdf_parser.py        # PyMuPDF text extraction
│   │   │   └── chunking.py          # Overlapping text chunker
│   │   └── jobs/
│   │       └── paper_processing.py  # Background embedding generation thread
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/001_initial_schema.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── hooks/
│   │   │   └── useAuth.ts           # Auth context + hooks
│   │   ├── services/
│   │   │   └── api.ts               # Axios API client
│   │   ├── types/
│   │   │   └── index.ts             # TypeScript interfaces
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── PaperCard.tsx
│   │   │   ├── WorkspaceCard.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   └── pages/
│   │       ├── Login/Login.tsx
│   │       ├── SearchPapers/SearchPapers.tsx
│   │       ├── Workspace/Workspace.tsx
│   │       └── Chatbot/Chatbot.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
└── docker-compose.yml
```

---

## Quick Start

### Prerequisites

- Docker Desktop running
- Node.js ≥ 18
- Python ≥ 3.10
- Groq API key → https://console.groq.com

---

### Step 1 — Start the Database

The PostgreSQL + pgvector container is already configured in `docker-compose.yml`.

```powershell
# From the workspace root (Research_Agent/)
docker compose up -d
```

Verify at: http://localhost:8080 (Adminer)

- System: PostgreSQL
- Server: db
- Username: Smartbridge
- Password: Smartbridge123
- Database: ResearchHub

---

### Step 2 — Configure Environment

```powershell
cd researchhub-ai\backend
copy .env.example .env
```

Edit `.env` and set your actual Groq API key:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=your-random-secret-key-here
DATABASE_URL=postgresql+psycopg2://Smartbridge:Smartbridge123@localhost:5432/ResearchHub
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Get a Groq API key at: https://console.groq.com/keys

---

### Step 3 — Backend Setup

```powershell
cd researchhub-ai\backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The database tables and pgvector extension are created automatically on startup.

API docs: http://localhost:8000/docs

---

### Step 4 — Frontend Setup

```powershell
cd researchhub-ai\frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend: http://localhost:3000

---

### Step 5 — Verify Full Workflow

1. **Register** — Create an account at http://localhost:3000/login
2. **Search** — Search for papers (e.g. "transformer attention") on the Search page
3. **Import** — Click "Import" on any result to save it; select a workspace
4. **Embed** — In Workspaces → open workspace → click ⚡ Embed on each paper
5. **Chat** — Click "💬 Chat with AI" to ask questions about your imported papers

---

## API Reference

| Method | Endpoint                        | Description                |
| ------ | ------------------------------- | -------------------------- |
| POST   | /auth/register                  | Register new user          |
| POST   | /auth/login                     | Login (returns JWT)        |
| GET    | /auth/me                        | Get current user           |
| GET    | /papers/search                  | Search arXiv/PubMed        |
| POST   | /papers/import                  | Import paper to DB         |
| POST   | /papers/{id}/process-embeddings | Generate vector embeddings |
| POST   | /workspaces/                    | Create workspace           |
| GET    | /workspaces/                    | List user workspaces       |
| GET    | /workspaces/{id}/papers         | List papers in workspace   |
| POST   | /workspaces/{id}/notes          | Create note                |
| POST   | /chat/session                   | Create chat session        |
| POST   | /chat/query                     | Send RAG query to AI       |
| GET    | /chat/messages/{session_id}     | Get chat history           |

---

## Database Schema

```
users ──────────── workspaces ─────── workspace_papers ── papers
  │                    │                                      │
  └── chat_sessions    └── notes                          paper_chunks
          │                                               (embedding vector)
          └── chat_messages
```

All UUIDs as primary keys · pgvector `vector(768)` for embeddings.

---

## RAG Pipeline

```
User Query
    │
    ▼
Convert to 768-dim embedding (all-mpnet-base-v2)
    │
    ▼
pgvector cosine similarity search → top-5 chunks
    │
    ▼
Retrieve chat history (last 6 messages)
    │
    ▼
Build RAG prompt:
  "Context from research papers: {chunks}
   Question: {query}
   Provide a clear research-focused answer…"
    │
    ▼
Groq llama-3.3-70b-versatile (temp=0.3)
    │
    ▼
Persist user + assistant messages
    │
    ▼
Return answer + source paper titles
```

---

## Development Notes

- **Embedding model**: `all-mpnet-base-v2` produces 768-dimensional vectors.
  The first run downloads ~420 MB; subsequent runs use the cached model.
- **PDF parsing**: Papers with a PDF URL are parsed via PyMuPDF.
  Abstracts serve as fallback when PDFs are inaccessible.
- **Background jobs**: Embedding generation runs in a daemon thread so
  import requests return immediately.
- **CORS**: Configured for `http://localhost:3000` and `http://localhost:5173`.

---

## Troubleshooting

| Issue                                      | Fix                                                |
| ------------------------------------------ | -------------------------------------------------- |
| `GROQ_API_KEY not set`                   | Add key to `backend/.env`                        |
| `vector type does not exist`             | Run `docker compose up -d` first                 |
| `Connection refused :5432`               | Ensure Docker Desktop is running                   |
| No embeddings / chat gives generic answers | Click ⚡ Embed on each paper                       |
| Frontend blank page                        | Run `npm install` in the `frontend/` directory |
