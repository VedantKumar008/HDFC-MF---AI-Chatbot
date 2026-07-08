# Environment Variables

Reference for all environment variables used across the HDFC MF AI Assistant monorepo.

## Root / Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes (Phase 4+) | — | API key from [Groq Console](https://console.groq.com/) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model ID; change when better free models are available |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed frontend origins |
| `DATA_PATH` | No | `./data/schemes` | Directory for scraped scheme JSON files |
| `FAISS_PATH` | No | `./data/faiss` | Directory for FAISS index artifacts |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence Transformers model name |

## Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | `http://localhost:8000` | FastAPI backend base URL |

## Production (Render — Backend)

```
GROQ_API_KEY=<secret>
GROQ_MODEL=llama-3.3-70b-versatile
CORS_ORIGINS=https://<your-vercel-app>.vercel.app
DATA_PATH=./data/schemes
FAISS_PATH=./data/faiss
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Production (Vercel — Frontend)

```
NEXT_PUBLIC_BACKEND_URL=https://<your-render-app>.onrender.com
```

## Setup

```powershell
# From project root
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
```

Never commit `.env` or `.env.local` files containing secrets.
