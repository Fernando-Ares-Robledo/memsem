from __future__ import annotations

import json
from pathlib import Path


def save_project(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2))


def load_project(path: Path) -> dict:
    return json.loads(path.read_text())
