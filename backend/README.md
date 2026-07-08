# Backend

FastAPI service for the HDFC MF AI Assistant.

## Run locally

From project root (with virtual environment active):

```powershell
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use `..\scripts\run-backend.ps1`.

Verify Phase 3:

```powershell
..\scripts\verify-phase3.ps1
```

## Endpoints (Phase 3)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness + readiness metadata |
| GET | `/schemes` | All 21 schemes with names, Groww URLs, and summary fields |
| POST | `/chat` | Placeholder (RAG streaming in Phase 4) |

### `GET /health`

Returns process status and knowledge-base load state:

- `ready`: `true` when schemes + FAISS index + embedding model are loaded
- `schemes_loaded`, `chunk_count`, `startup_seconds`
- `index_built_at` from FAISS manifest

Render uses this path as the health check. The endpoint returns HTTP 200 once the process is running; use the `ready` field for readiness.

### `GET /schemes`

Returns scraped scheme summaries for the frontend sidebar:

```json
{
  "count": 21,
  "schemes": [
    {
      "id": "hdfc-defence-fund-direct-growth",
      "name": "HDFC Defence Fund Direct Growth",
      "url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
      "category": "Equity",
      "nav": 30.444,
      "expense_ratio": 0.87
    }
  ]
}
```

### `POST /chat` (placeholder)

```json
{
  "message": "What is the NAV of HDFC Defence Fund?",
  "session_id": "uuid"
}
```

## Startup sequence

On application startup the backend:

1. Loads scraped JSON summaries from `data/schemes/`
2. Loads FAISS index + chunk metadata from `data/faiss/`
3. Loads the Sentence Transformers embedding model
4. Marks the app `ready` and exposes status via `/health`

## Cold start (Render free tier)

The first request after a cold start can take **20-40 seconds** while the embedding model and FAISS index load into memory. The frontend should show a warming message until `/health` reports `ready: true`.

Subsequent requests are much faster; vector retrieval target is under 1 second.

## Deployment (Render)

Use the root `render.yaml` or configure manually:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Health check:** `/health`

Set `CORS_ORIGINS` to your Vercel frontend URL in production.
