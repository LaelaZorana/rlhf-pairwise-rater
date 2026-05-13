"""The terminal-prompt UX for rating a case."""
from __future__ import annotations

AXES = ["helpfulness", "harmlessness", "accuracy", "instruction_following"]


def _ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"  Enter {lo}-{hi}.")


def _ask_choice(prompt: str, choices: list[str]) -> str:
    cl = [c.lower() for c in choices]
    while True:
        raw = input(prompt).strip().lower()
        if raw in cl:
            return raw.upper()


def rate_case(case: dict, rater: str) -> dict:
    print("=" * 70)
    print(f"id: {case.get('id')}")
    print(f"PROMPT: {case.get('prompt')}")
    print(f"A: {case.get('response_a')}")
    print(f"B: {case.get('response_b')}")
    scores_a = {ax: _ask_int(f"  A {ax} (1-5): ", 1, 5) for ax in AXES}
    scores_b = {ax: _ask_int(f"  B {ax} (1-5): ", 1, 5) for ax in AXES}
    preference = _ask_choice("Pref (A/B/TIE): ", ["A", "B", "TIE"])
    confidence = _ask_int("Confidence (1-5): ", 1, 5)
    return {"id": case.get("id"), "rater": rater,
            "scores_a": scores_a, "scores_b": scores_b,
            "preference": preference, "confidence": confidence}
