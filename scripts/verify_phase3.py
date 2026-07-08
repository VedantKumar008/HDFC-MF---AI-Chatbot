"""Validate Phase 3 FastAPI backend endpoints."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from shared.schemes import APPROVED_SCHEME_COUNT, load_schemes

from backend.app.main import app


def main() -> int:
    errors: list[str] = []
    manifest = load_schemes()

    with TestClient(app) as client:
        health = client.get("/health")
        if health.status_code != 200:
            errors.append(f"/health returned {health.status_code}")
        else:
            payload = health.json()
            if not payload.get("ready"):
                errors.append("/health ready=false after startup")
            if payload.get("schemes_loaded") != APPROVED_SCHEME_COUNT:
                errors.append(
                    f"/health schemes_loaded={payload.get('schemes_loaded')} "
                    f"expected {APPROVED_SCHEME_COUNT}"
                )
            if not payload.get("index_loaded"):
                errors.append("/health index_loaded=false")
            if not payload.get("embedding_model_loaded"):
                errors.append("/health embedding_model_loaded=false")
            if payload.get("chunk_count", 0) <= 0:
                errors.append("/health chunk_count missing")

        schemes_response = client.get("/schemes")
        if schemes_response.status_code != 200:
            errors.append(f"/schemes returned {schemes_response.status_code}")
        else:
            body = schemes_response.json()
            if body.get("count") != APPROVED_SCHEME_COUNT:
                errors.append(f"/schemes count={body.get('count')} expected {APPROVED_SCHEME_COUNT}")
            schemes = body.get("schemes") or []
            manifest_by_id = {item["id"]: item for item in manifest}
            for scheme in schemes:
                scheme_id = scheme.get("id")
                if not scheme.get("name") or not scheme.get("url"):
                    errors.append(f"/schemes entry missing name/url for {scheme_id}")
                expected = manifest_by_id.get(scheme_id)
                if expected and scheme.get("url") != expected["url"]:
                    errors.append(f"/schemes url mismatch for {scheme_id}")

        chat_response = client.post(
            "/chat",
            json={
                "message": "What is the expense ratio of HDFC Defence Fund?",
                "session_id": "phase3-test-session",
            },
        )
        if chat_response.status_code != 200:
            errors.append(f"/chat returned {chat_response.status_code}")
        elif not chat_response.json().get("placeholder"):
            errors.append("/chat placeholder flag not set")

        cors_response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
        allow_origin = cors_response.headers.get("access-control-allow-origin")
        if allow_origin not in {"http://localhost:3000", "*"}:
            errors.append(f"CORS header missing/incorrect: {allow_origin}")

    if errors:
        print("Phase 3 verification FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: /health reports ready with FAISS index loaded")
    print(f"OK: /schemes returns {APPROVED_SCHEME_COUNT} schemes with Groww URLs")
    print("OK: /chat placeholder responds successfully")
    print("OK: CORS configured for frontend origin")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
