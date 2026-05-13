"""Summary stats."""
from __future__ import annotations

from collections import Counter

from .prompts import AXES


def summarize(ratings: list[dict]) -> dict:
    if not ratings:
        return {"total": 0}
    pref_counts = Counter(r["preference"] for r in ratings)
    mean_conf = sum(r["confidence"] for r in ratings) / len(ratings)
    axis_a = {ax: sum(r["scores_a"][ax] for r in ratings) / len(ratings) for ax in AXES}
    axis_b = {ax: sum(r["scores_b"][ax] for r in ratings) / len(ratings) for ax in AXES}
    return {"total": len(ratings),
            "preference_counts": dict(pref_counts),
            "mean_confidence": round(mean_conf, 2),
            "axis_means_a": {k: round(v, 2) for k, v in axis_a.items()},
            "axis_means_b": {k: round(v, 2) for k, v in axis_b.items()}}
