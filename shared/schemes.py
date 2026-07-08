"""Load the approved scheme manifest shared across Python sub-projects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict


class Scheme(TypedDict):
    id: str
    name: str
    url: str


class SchemeManifest(TypedDict):
    version: int
    description: str
    schemes: list[Scheme]


MANIFEST_PATH = Path(__file__).resolve().parent / "schemes.json"
APPROVED_SCHEME_COUNT = 21


def load_manifest(path: Path | None = None) -> SchemeManifest:
    manifest_path = path or MANIFEST_PATH
    with manifest_path.open(encoding="utf-8") as manifest_file:
        manifest: SchemeManifest = json.load(manifest_file)

    schemes = manifest.get("schemes", [])
    if len(schemes) != APPROVED_SCHEME_COUNT:
        raise ValueError(
            f"Expected {APPROVED_SCHEME_COUNT} approved schemes, found {len(schemes)}."
        )

    return manifest


def load_schemes(path: Path | None = None) -> list[Scheme]:
    return load_manifest(path)["schemes"]
