# 🔍 Research Agent

> An AI-powered research agent that searches the web and synthesizes cited reports from real sources — streaming live to your browser.

**🌐 Live Demo:** [research-agent-pi-nine.vercel.app](https://research-agent-pi-nine.vercel.app)  

---

## ✨ What It Does

Ask any question. The agent:

1. **Rewrites** your question into a targeted web search query
2. **Searches** the web via Tavily and fetches the top 4 sources
3. **Synthesizes** a structured, cited markdown report using Google Gemini
4. **Streams** the report token-by-token to your browser in real time
5. **Persists** everything to Postgres so you can revisit it later

Every claim in the report cites a numbered source, so you can verify what the AI says.

---

## 🎯 Features

- **JWT Authentication** — register, login, and secure all endpoints
- **Live Streaming** — see the report being written in real time (Server-Sent Events)
- **Cited Reports** — structured markdown with `[1]`, `[2]` citations linked to sources
- **Persistent History** — every research job is saved to your account
- **Multi-Stage Pipeline** — query rewriting, web search, and synthesis as distinct stages
- **Background Jobs** — long-running research runs asynchronously (non-blocking)
- **User-Scoped Data** — you can only see your own research
- **Responsive UI** — works on desktop and mobile

---

## 🛠 Tech Stack

### Backend
| Layer | Tech |
|---|---|
| API Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Database | PostgreSQL (Neon serverless) |
| LLM | Google Gemini (`langchain-google-genai`) |
| Web Search | Tavily API |
| Streaming | Server-Sent Events (SSE) |

### Frontend
| Layer | Tech |
|---|---|
| Framework | React 19 + TypeScript |
| Build Tool | Vite |
| Routing | React Router v6 |
| Styling | Tailwind CSS v4 |
| Markdown | react-markdown |

### Infrastructure
| Layer | Tech |
|---|---|
| Frontend Host | Vercel |
| Backend Host | Render |
| Database | Neon Postgres |
| Version Control | GitHub |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (React + TypeScript + Tailwind)                │
│  ├── Login / Register → JWT stored                      │
│  ├── Dashboard → list of past research                  │
│  ├── New Research → LIVE token streaming (SSE)          │
│  └── Detail → markdown report + sources                 │
└──────────────────────┬──────────────────────────────────┘
                       │  HTTPS + JWT
                       ▼
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend (Render)                               │
│  ├── Auth (JWT + bcrypt)                                │
│  ├── POST /research/         (background job)           │
│  ├── POST /research/stream   (SSE live streaming)       │
│  ├── GET  /research/         (user-scoped list)         │
│  └── GET  /research/{id}     (detail with sources)      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  AI Pipeline                                            │
│  ├── Query rewriting  → Gemini 3.5 Flash-Lite           │
│  ├── Web search       → Tavily API                      │
│  └── Report synthesis → Gemini 3.8 Flash (streamed)     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│  Neon Postgres                                          │
│  ├── users                                              │
│  ├── researches                                         │
│  └── sources                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Neon Postgres database ([neon.tech](https://neon.tech))
- A Gemini API key ([ai.google.dev](https://ai.google.dev))
- A Tavily API key ([tavily.com](https://tavily.com))

### 1. Clone the Repository

```bash
git clone https://github.com/surajrastogi1/Research-Agent.git
cd Research-Agent
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Neon pooled connection string (for the app)
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require

# Neon direct connection string (for migrations)
DATABASE_URL_DIRECT=postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require

# JWT
SECRET_KEY=your-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI services
GEMINI_API_KEY=your-gemini-key
TAVILY_API_KEY=your-tavily-key

# CORS
CORS_ORIGINS=http://localhost:5173
```

Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Run migrations and start the server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Backend is now at `http://127.0.0.1:8000` — Swagger docs at `/docs`.

### 3. Frontend Setup

```bash
cd research-agent-frontend

# Install dependencies
npm install

# Copy env
cp .env.example .env
```

Edit `.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the dev server:

```bash
npm run dev
```

Frontend is now at `http://localhost:5173`.

---

## 📡 API Endpoints

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Get a JWT access token |
| `GET` | `/auth/me` | Get the current user |

### Research

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/research/` | Create a research job (background task, returns 202) |
| `POST` | `/research/stream` | Same pipeline, but streamed live via SSE |
| `GET` | `/research/` | List all research for the current user |
| `GET` | `/research/{id}` | Get a specific research with its sources |

All research endpoints require an `Authorization: Bearer <token>` header.

### SSE Event Format

The `/research/stream` endpoint emits these events:

```
event: research_id
data: {"id": "..."}

event: status
data: {"stage": "generating_query"}

event: status
data: {"stage": "searching", "query": "what is alembic"}

event: sources
data: [{ "title": "...", "url": "...", "content": "..." }]

event: status
data: {"stage": "synthesizing"}

event: token
data: {"text": "Alembic"}

event: token
data: {"text": " is"}

... hundreds more tokens ...

event: done
data: {"report": "...", "sources": [...]}
```

---

## 🎬 How It Works — Deep Dive

### 1. Query Rewriting

The user's question might be long-form ("Can you tell me how Alembic handles migrations in multi-tenant Postgres?"). The agent calls Gemini to rewrite it as a keyword-friendly search query (`"Alembic migrations multi-tenant Postgres"`).

### 2. Web Search

Tavily returns clean, LLM-friendly results — title, URL, and a text snippet. This is different from scraping Google, which would return raw HTML noise.

### 3. Grounded Synthesis

The synthesis prompt includes all sources as numbered context blocks. The LLM is instructed to answer **using ONLY the provided sources** and cite them as `[1]`, `[2]`. This prevents hallucination.

### 4. Token Streaming

Gemini's `.stream()` yields tokens as they're generated. FastAPI wraps this in a `StreamingResponse` with `text/event-stream`. The browser reads chunks via `fetch()` + `ReadableStream` and appends each token to state — producing the live typing effect.

### 5. Persistence

After the stream completes, sources are saved as `Source` rows linked to the `Research` row via foreign key. The client can revisit anytime at `/research/{id}`.

---

## 📂 Project Structure

```
Research-Agent/
├── app/
│   ├── api/
│   │   ├── deps.py                # get_current_user, get_db
│   │   └── routes/
│   │       ├── auth.py            # register, login, me
│   │       └── research.py        # create, list, get, stream
│   ├── core/
│   │   └── security.py            # JWT + bcrypt helpers
│   ├── db/
│   │   └── session.py             # engine, SessionLocal, get_db
│   ├── models/
│   │   └── models.py              # User, Research, Source
│   ├── schemas/
│   │   ├── user.py                # UserCreate, UserResponse, Token
│   │   └── research.py            # ResearchCreate, ResearchResponse, SourceResponse
│   ├── services/
│   │   ├── search_service.py      # Tavily wrapper
│   │   └── research_service.py    # Pipeline + background task
│   └── main.py                    # FastAPI app + CORS
├── alembic/                       # DB migrations
├── requirements.txt
├── .env.example
└── research-agent-frontend/
    ├── src/
    │   ├── lib/api.ts             # fetch wrapper + auth helpers
    │   ├── components/Navbar.tsx
    │   ├── pages/
    │   │   ├── Login.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── NewResearch.tsx    # Live SSE streaming
    │   │   └── ResearchDetail.tsx
    │   ├── App.tsx
    │   └── main.tsx
    ├── vercel.json                # SPA rewrite config
    └── package.json
```

---

## 🌐 Deployment

### Backend — Render

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Set **Root Directory** to the repo root
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (same as `.env`)

### Frontend — Vercel

1. Import the repo on [vercel.com](https://vercel.com)
2. Set **Root Directory** to `research-agent-frontend`
3. Framework preset: **Vite**
4. Add env var: `VITE_API_URL=https://your-backend.onrender.com`
5. Deploy

**Important:** After deploying the frontend, add its URL to Render's `CORS_ORIGINS`:

```
CORS_ORIGINS=http://localhost:5173,https://your-app.vercel.app
```

### Database — Neon

1. Create a project on [neon.tech](https://neon.tech)
2. Copy **both** connection strings:
   - **Pooled** → `DATABASE_URL` (used by the running app)
   - **Direct** → `DATABASE_URL_DIRECT` (used by Alembic migrations)
3. Run migrations: `python -m alembic upgrade head`

---

## 🧪 Testing the API

Register a user:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Copy the `access_token` and stream a research request:

```bash
curl -N -X POST http://127.0.0.1:8000/research/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Alembic?"}'
```

You should see SSE events arriving in real time.

---

## ⚠️ Known Limitations (V1)

- Synchronous background processing — jobs run in the API process (moving to Celery + Redis in V2)
- Gemini free tier: **20 requests/day per model** — the app may hit quota during heavy use
- Render free tier spins down after 15 minutes idle (first request after wake: ~30s)
- No rate limiting per user
- No shareable public reports
- No follow-up questions

---

## 🗺 Roadmap (V2)

- [ ] Celery + Redis for real distributed background workers
- [ ] Multi-query research (generate 3–5 sub-queries per question)
- [ ] Follow-up questions with conversation context
- [ ] Per-user rate limiting
- [ ] Public shareable report links
- [ ] Copy / export report as PDF
- [ ] Dark mode

---

## 🤝 Contributing

This is a personal learning project, but feedback and suggestions are welcome. Open an issue or start a discussion.

---

## 📄 License

MIT — free to use, modify, and learn from.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [Google Gemini](https://ai.google.dev/) — LLM for query rewriting and synthesis
- [Tavily](https://tavily.com/) — LLM-optimized web search
- [Neon](https://neon.tech/) — serverless Postgres
- [Vercel](https://vercel.com/) & [Render](https://render.com/) — free-tier hosting
- [Tailwind CSS](https://tailwindcss.com/) — styling

---

**Built as a learning project to explore the full stack of modern AI applications — from streaming LLM output to serverless Postgres to production deployment.**