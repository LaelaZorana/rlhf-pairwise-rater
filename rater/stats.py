"""Summary stats and inter-rater agreement."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from .prompts import AXES


def summarize(ratings: list[dict]) -> dict:
    """Compute summary stats over a list of ratings."""
    if not ratings:
        return {"total": 0}

    pref_counts = Counter(r["preference"] for r in ratings)
    mean_conf = sum(r["confidence"] for r in ratings) / len(ratings)

    axis_means_a = {ax: _safe_mean([r["scores_a"][ax] for r in ratings]) for ax in AXES}
    axis_means_b = {ax: _safe_mean([r["scores_b"][ax] for r in ratings]) for ax in AXES}

    # Self-consistency: if you said "A wins" but scored B higher on every axis, that's odd.
    inconsistencies = []
    for r in ratings:
        pref = r["preference"]
        if pref == "TIE":
            continue
        winner_scores = r["scores_a"] if pref == "A" else r["scores_b"]
        loser_scores = r["scores_b"] if pref == "A" else r["scores_a"]
        if all(loser_scores[ax] > winner_scores[ax] for ax in AXES):
            inconsistencies.append(r["id"])

    return {
        "total": len(ratings),
        "preference_counts": dict(pref_counts),
        "mean_confidence": round(mean_conf, 2),
        "axis_means_a": {k: round(v, 2) for k, v in axis_means_a.items()},
        "axis_means_b": {k: round(v, 2) for k, v in axis_means_b.items()},
        "self_consistency_flags": inconsistencies,
    }


def _safe_mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def cohens_kappa(labels_1: list[str], labels_2: list[str]) -> float:
    """Cohen's kappa for two raters over a categorical label sequence.

    Returns 0.0 if both lists agree at chance level, 1.0 for perfect agreement,
    negative values when agreement is worse than chance.
    """
    if len(labels_1) != len(labels_2):
        raise ValueError("Label lists must be the same length")
    if not labels_1:
        return 0.0

    n = len(labels_1)
    categories = sorted(set(labels_1) | set(labels_2))
    observed_agreement = sum(1 for a, b in zip(labels_1, labels_2) if a == b) / n

    expected_agreement = 0.0
    for c in categories:
        p1 = labels_1.count(c) / n
        p2 = labels_2.count(c) / n
        expected_agreement += p1 * p2

    if expected_agreement >= 1.0:
        return 1.0
    return (observed_agreement - expected_agreement) / (1 - expected_agreement)


def agreement_between(ratings_1: list[dict], ratings_2: list[dict]) -> dict:
    """Compare two raters who rated overlapping cases. Returns kappa + breakdown."""
    by_id_1 = {r["id"]: r for r in ratings_1}
    by_id_2 = {r["id"]: r for r in ratings_2}
    common = sorted(set(by_id_1) & set(by_id_2))

    if not common:
        return {"common_cases": 0, "kappa": None}

    prefs_1 = [by_id_1[i]["preference"] for i in common]
    prefs_2 = [by_id_2[i]["preference"] for i in common]
    kappa = cohens_kappa(prefs_1, prefs_2)

    disagreements = [
        (i, by_id_1[i]["preference"], by_id_2[i]["preference"])
        for i in common
        if by_id_1[i]["preference"] != by_id_2[i]["preference"]
    ]

    return {
        "common_cases": len(common),
        "kappa": round(kappa, 3),
        "disagreements": disagreements,
    }
