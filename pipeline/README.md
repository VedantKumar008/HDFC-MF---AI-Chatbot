# Pipeline (Phase 2)

Builds a FAISS vector index from scraped scheme JSON files for RAG retrieval.

## How it works

1. Load all `data/schemes/*.json` files (21 approved schemes)
2. Chunk by logical sections (overview, holdings, returns, tax, FAQ, etc.)
3. Embed chunks with Sentence Transformers (`all-MiniLM-L6-v2`)
4. Build a cosine-similarity FAISS index (`IndexFlatIP` with normalized vectors)
5. Write artifacts to `data/faiss/`

## Run

From project root:

```powershell
.\scripts\run-index-builder.ps1
.\scripts\verify-phase2.ps1
```

Direct CLI:

```powershell
python -m pipeline.pipeline
```

## Output artifacts

| File | Purpose |
|------|---------|
| `index.faiss` | FAISS vector store |
| `chunks.json` | Chunk text + metadata mapped by `chunk_id` |
| `manifest.json` | Build metadata (model, counts, timestamp) |

Each chunk includes: `scheme_name`, `scheme_url`, `section`, `scraped_at`, and `text`.

## Notes

- Requires Phase 1 scraped JSON in `data/schemes/`
- First run downloads the embedding model (~90MB)
- Artifacts are designed to be committed to the repository for Render deployment
