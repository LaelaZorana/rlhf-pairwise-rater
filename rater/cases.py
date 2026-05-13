"""JSONL reading and writing for comparison cases and ratings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def read_cases(path: str | Path) -> Iterator[dict]:
    """Yield each JSON object from a JSONL file. Skips blank lines."""
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path} line {i}: invalid JSON: {e}") from e


def append_rating(path: str | Path, rating: dict) -> None:
    """Append a single rating dict to a JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rating, ensure_ascii=False) + "\n")


def read_ratings(path: str | Path) -> list[dict]:
    return list(read_cases(path))
