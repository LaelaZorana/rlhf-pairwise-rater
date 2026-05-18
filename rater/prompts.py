"""The terminal-prompt UX for rating a case."""
from __future__ import annotations

AXES = ["helpfulness", "harmlessness", "accuracy", "instruction_following"]
AXIS_DESCRIPTIONS = {
    "helpfulness": "Does it actually answer / address the prompt?",
    "harmlessness": "Anything unsafe, misleading, biased, or potentially harmful?",
    "accuracy": "Is the factual content correct?",
    "instruction_following": "Did it follow what was asked (format, length, tone, constraints)?",
}


def _ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            v = int(raw)
        except ValueError:
            print(f"  Please enter an integer between {lo} and {hi}.")
            continue
        if v < lo or v > hi:
            print(f"  Out of range. {lo}–{hi}.")
            continue
        return v


def _ask_choice(prompt: str, choices: list[str]) -> str:
    choices_lower = [c.lower() for c in choices]
    while True:
        raw = input(prompt).strip().lower()
        if raw in choices_lower:
            return raw.upper()
        print(f"  Please enter one of: {', '.join(choices)}")


def rate_case(case: dict, rater: str) -> dict:
    """Walk the user through rating a single comparison case interactively."""
    print("\n" + "=" * 70)
    print(f"Case id: {case.get('id', '?')}")
    print(f"\nPROMPT:\n  {case.get('prompt', '')}")
    print(f"\n--- RESPONSE A ---\n{case.get('response_a', '')}")
    print(f"\n--- RESPONSE B ---\n{case.get('response_b', '')}")
    print("-" * 70)

    scores_a: dict[str, int] = {}
    scores_b: dict[str, int] = {}
    for axis in AXES:
        print(f"\n[{axis}] {AXIS_DESCRIPTIONS[axis]}")
        scores_a[axis] = _ask_int(f"  Score A (1–5): ", 1, 5)
        scores_b[axis] = _ask_int(f"  Score B (1–5): ", 1, 5)

    preference = _ask_choice("\nOverall preference (A / B / TIE): ", ["A", "B", "TIE"])
    confidence = _ask_int("How confident in that preference? (1–5): ", 1, 5)
    reason = input("One-line reason (optional, press Enter to skip): ").strip()

    return {
        "id": case.get("id"),
        "rater": rater,
        "scores_a": scores_a,
        "scores_b": scores_b,
        "preference": preference,
        "confidence": confidence,
        "reason": reason or None,
    }
