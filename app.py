"""
Gradio demo for the RLHF Pairwise Response Rater.

Two things this tool does that a plain rating form does not:
  1. Self-consistency check — flags when you pick a winner but score the loser
     higher on every axis (a real, common rater mistake).
  2. Inter-rater agreement — Cohen's kappa between two raters, so you can see
     whether two people are actually applying the same standard.

Both run the real package code in rater/stats.py — the same functions covered
by the pytest suite.

Run locally:   pip install -r requirements.txt && python app.py
On Hugging Face Spaces this file is the entry point (app_file: app.py).
"""
from __future__ import annotations

import json
import glob
from pathlib import Path

import gradio as gr

from rater import stats
from rater.prompts import AXES, AXIS_DESCRIPTIONS


def _load_cases() -> list:
    cases = []
    for path in sorted(glob.glob("examples/*.jsonl")):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        cases.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            continue
    return cases


CASES = _load_cases()
CASE_LABELS = [f"{c['id']}: {c['prompt'][:60]}" for c in CASES]


def pick_case(label: str):
    if not label:
        return "", "", ""
    idx = CASE_LABELS.index(label)
    c = CASES[idx]
    return c["prompt"], c["response_a"], c["response_b"]


def rate(prompt, resp_a, resp_b,
         h_a, h_b, harm_a, harm_b, acc_a, acc_b, if_a, if_b,
         preference, confidence):
    """Build a rating record and run the real self-consistency check on it."""
    rating = {
        "id": "demo",
        "preference": preference,
        "confidence": int(confidence),
        "scores_a": {
            "helpfulness": int(h_a), "harmlessness": int(harm_a),
            "accuracy": int(acc_a), "instruction_following": int(if_a),
        },
        "scores_b": {
            "helpfulness": int(h_b), "harmlessness": int(harm_b),
            "accuracy": int(acc_b), "instruction_following": int(if_b),
        },
    }
    summary = stats.summarize([rating])
    flagged = "demo" in summary.get("self_consistency_flags", [])

    lines = [f"### Preference: **{preference}**  ·  confidence {int(confidence)}/5", ""]
    if flagged:
        lines.append(
            f"> ⚠️ **Self-consistency flag.** You preferred **{preference}**, but the "
            "other response scored higher on *every* axis. Re-check the call — this is "
            "exactly the kind of silent rating error the tool is built to catch."
        )
    else:
        lines.append("> ✅ No self-consistency conflict — your preference lines up with your axis scores.")
    lines += ["", "**Rating record (JSONL):**", "```json", json.dumps(rating), "```"]
    return "\n".join(lines)


KAPPA_EXAMPLE_1 = "\n".join(json.dumps(r) for r in [
    {"id": "001", "preference": "A"}, {"id": "002", "preference": "B"},
    {"id": "003", "preference": "B"}, {"id": "004", "preference": "A"},
    {"id": "005", "preference": "TIE"},
])
KAPPA_EXAMPLE_2 = "\n".join(json.dumps(r) for r in [
    {"id": "001", "preference": "A"}, {"id": "002", "preference": "B"},
    {"id": "003", "preference": "A"}, {"id": "004", "preference": "A"},
    {"id": "005", "preference": "B"},
])


def _parse_jsonl(text: str) -> list:
    out = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def agreement(rater1_text, rater2_text):
    try:
        r1 = _parse_jsonl(rater1_text)
        r2 = _parse_jsonl(rater2_text)
    except json.JSONDecodeError as exc:
        return f"❌ Invalid JSONL — {exc}"

    result = stats.agreement_between(r1, r2)
    if not result.get("common_cases"):
        return "No overlapping case IDs between the two raters."

    kappa = result["kappa"]
    if kappa is None:
        interp = ""
    elif kappa >= 0.8:
        interp = "almost perfect agreement"
    elif kappa >= 0.6:
        interp = "substantial agreement"
    elif kappa >= 0.4:
        interp = "moderate agreement"
    elif kappa >= 0.2:
        interp = "fair agreement"
    else:
        interp = "poor / near-chance agreement — the rubric may be ambiguous, or a rater has drifted"

    lines = [
        f"### Cohen's κ = **{kappa}**  ({interp})",
        f"Compared **{result['common_cases']}** overlapping cases.",
        "",
    ]
    disagreements = result.get("disagreements", [])
    if disagreements:
        lines.append("**Where the two raters disagreed:**")
        lines.append("")
        lines.append("| Case | Rater 1 | Rater 2 |")
        lines.append("|---|---|---|")
        for cid, p1, p2 in disagreements:
            lines.append(f"| {cid} | {p1} | {p2} |")
    else:
        lines.append("No disagreements on the overlapping cases.")
    return "\n".join(lines)


with gr.Blocks(title="RLHF Pairwise Response Rater") as demo:
    gr.Markdown(
        "# ⚖️ RLHF Pairwise Response Rater\n"
        "The workflow behind preference data for RLHF — rate two model responses on four "
        "axes, pick a winner, and the tool checks your work. It catches **self-consistency "
        "errors** (you picked A but scored B higher everywhere) and measures **inter-rater "
        "agreement** with Cohen's kappa, so you can tell whether two people are really "
        "applying the same standard.\n\n"
        "*Runs the real package (`rater/stats.py`), the same code the pytest suite covers.*"
    )

    with gr.Tab("Rate a pair"):
        case_dd = gr.Dropdown(choices=CASE_LABELS, label="Load an example case",
                              value=CASE_LABELS[0] if CASE_LABELS else None)
        prompt_box = gr.Textbox(label="Prompt", lines=2)
        with gr.Row():
            a_box = gr.Textbox(label="Response A", lines=6)
            b_box = gr.Textbox(label="Response B", lines=6)

        gr.Markdown("**Score each response 1–5 on every axis** "
                    + " · ".join(f"*{a}*: {AXIS_DESCRIPTIONS[a]}" for a in AXES))
        with gr.Row():
            with gr.Column():
                gr.Markdown("**Response A**")
                h_a = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_a = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_a = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_a = gr.Slider(1, 5, value=3, step=1, label="instruction_following")
            with gr.Column():
                gr.Markdown("**Response B**")
                h_b = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_b = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_b = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_b = gr.Slider(1, 5, value=3, step=1, label="instruction_following")

        with gr.Row():
            preference = gr.Radio(["A", "B", "TIE"], value="A", label="Overall preference")
            confidence = gr.Slider(1, 5, value=3, step=1, label="Confidence")

        rate_btn = gr.Button("Check my rating", variant="primary")
        rate_out = gr.Markdown()

        case_dd.change(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])
        rate_btn.click(
            rate,
            inputs=[prompt_box, a_box, b_box, h_a, h_b, harm_a, harm_b,
                    acc_a, acc_b, if_a, if_b, preference, confidence],
            outputs=rate_out,
        )

    with gr.Tab("Inter-rater agreement (Cohen's κ)"):
        gr.Markdown(
            "Paste each rater's ratings as JSONL (one object per line, each with an "
            "`id` and a `preference` of `A` / `B` / `TIE`). The tool matches on shared "
            "case IDs and computes Cohen's kappa."
        )
        with gr.Row():
            r1_box = gr.Textbox(label="Rater 1 (JSONL)", value=KAPPA_EXAMPLE_1, lines=8)
            r2_box = gr.Textbox(label="Rater 2 (JSONL)", value=KAPPA_EXAMPLE_2, lines=8)
        kappa_btn = gr.Button("Compute agreement", variant="primary")
        kappa_out = gr.Markdown()
        kappa_btn.click(agreement, inputs=[r1_box, r2_box], outputs=kappa_out)

    demo.load(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])


if __name__ == "__main__":
    demo.launch()
