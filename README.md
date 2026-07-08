# HDFC Mutual Fund AI Assistant

ChatGPT-inspired AI assistant for factual information about 21 approved HDFC Mutual Fund schemes. **Phase 0** scaffolds the monorepo; **Phase 1** scrapes Groww data; **Phase 2** builds the FAISS vector index.

## Prerequisites

- **Python** 3.11+
- **Node.js** 20+
- **npm** 10+
- **Groq API key** (required from Phase 4 onward)

## Project structure

```
hdfc-mf-ai-assistant/
├── frontend/          # Next.js + TypeScript + Tailwind (Vercel)
├── backend/           # FastAPI (Render)
├── scraper/           # Groww scraper (Phase 1)
├── pipeline/          # FAISS index builder (Phase 2)
├── shared/            # Scheme manifest (single source of truth)
│   └── schemes.json   # Synced to frontend via scripts/sync-schemes.ps1
├── data/
│   ├── schemes/       # Scraped JSON (Phase 1+)
│   └── faiss/         # Vector index (Phase 2+)
├── docs/              # Environment variable reference
└── scripts/           # Setup and run helpers
```

## Quick start (Windows)

```powershell
cd hdfc-mf-ai-assistant
.\scripts\setup.ps1
.\scripts\verify-phase0.ps1
```

### Run services locally

**Terminal 1 — Backend**

```powershell
.\scripts\run-backend.ps1
```

API: http://localhost:8000  
Health: http://localhost:8000/health  
Schemes: http://localhost:8000/schemes

**Terminal 2 — Frontend**

```powershell
.\scripts\run-frontend.ps1
```

App: http://localhost:3000

### Scrape scheme data (Phase 1)

```powershell
.\scripts\run-scraper.ps1
.\scripts\verify-phase1.ps1
```

Output: `data/schemes/<scheme-id>.json` (21 files)

### Build FAISS index (Phase 2)

```powershell
.\scripts\run-index-builder.ps1
.\scripts\verify-phase2.ps1
```

Output: `data/faiss/index.faiss`, `chunks.json`, `manifest.json`

## Manual setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
cd frontend && npm install && cd ..
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
```

## Environment variables

See [docs/environment-variables.md](docs/environment-variables.md).

## Phase 0 exit criteria

- [x] Monorepo layout (`frontend/`, `backend/`, `scraper/`, `pipeline/`, `data/`)
- [x] Python + Node dependencies defined
- [x] Shared scheme manifest with exactly **21** approved Groww URLs
- [x] Environment variable templates
- [x] Local run scripts and README

## Phase 1 exit criteria

- [x] Groww scraper fetches all **21** approved schemes
- [x] Structured JSON written to `data/schemes/`
- [x] Each file retains its original Groww URL and scrape timestamp
- [x] Standalone CLI: `python -m scraper.scraper`

## Phase 2 exit criteria

- [x] FAISS index rebuilds from JSON (~34s locally, 523 chunks)
- [x] Sample queries return relevant chunks for known questions
- [x] Artifacts in `data/faiss/` are loadable (`index.faiss`, `chunks.json`, `manifest.json`)

## Phase 3 exit criteria

- [x] FastAPI backend with `/health`, `/schemes`, `/chat` placeholder
- [x] Startup loads schemes + FAISS + embedding model
- [x] CORS configured for frontend origin
- [x] Render-compatible `render.yaml`

## Phase 4 exit criteria

- [x] RAG pipeline retrieves relevant chunks from FAISS index
- [x] Groq LLM integration for answer generation
- [x] Token-by-token streaming via Server-Sent Events (SSE)
- [x] Average end-to-end response time under 5 seconds
- [x] Vector retrieval under 1 second
- [x] Out-of-scope queries handled gracefully
- [x] Factual answers based on indexed HDFC scheme data

## Phase 5 exit criteria

- [x] Investment advice patterns blocked before LLM generation
- [x] Out-of-scope fund house queries blocked with scope message
- [x] Low-confidence retrieval returns anti-hallucination message
- [x] Compliance layer integrated into chat endpoint
- [x] Standard refusal messages for blocked categories
- [x] Factual HDFC queries allowed through compliance checks

## Phase 6 exit criteria

- [x] In-memory session store with conversation history
- [x] Session context passed to RAG pipeline for follow-up queries
- [x] Pronoun and follow-up queries resolve correctly within session
- [x] New sessions start with empty context
- [x] Session isolation maintained between different session IDs
- [x] No chat history survives server restart (in-memory only)

## Phase 7 exit criteria

- [x] ChatGPT-inspired UI with sidebar and main chat area
- [x] Streaming responses via SSE from backend
- [x] Markdown rendering for assistant responses
- [x] Scheme sidebar with Groww links (21 approved schemes)
- [x] Suggested prompts on welcome screen
- [x] Mobile-responsive design with collapsible sidebar
- [x] Cold start loading state for backend wake-up
- [x] Session management with new chat functionality

## Phase 8 exit criteria

- [x] GitHub Actions workflow for daily data refresh
- [x] Scheduled workflow at 9:00 AM IST (3:30 AM UTC)
- [x] Scraper step to fetch latest Groww data
- [x] FAISS index rebuild step
- [x] Git commit and push for data changes
- [x] Validation checks (21 schemes, index artifacts)
- [x] Manual workflow dispatch capability

## Phase 9 exit criteria

- [x] Render deployment configuration (render.yaml)
- [x] Vercel deployment configuration (vercel.json)
- [x] Environment variable documentation for production
- [x] Deployment guide with step-by-step instructions
- [x] Free-tier configuration (Render + Vercel)
- [x] CORS configuration for cross-origin requests
- [x] Health check endpoint for monitoring
- [x] Post-deployment verification procedures

## Next phases

| Phase | Deliverable |
|-------|-------------|
| 4–6 | RAG streaming, compliance, session memory |
| 7 | ChatGPT-style streaming UI |
| 8–9 | GitHub Actions daily refresh + deployment |

## License

Internal / educational use per project specification.
