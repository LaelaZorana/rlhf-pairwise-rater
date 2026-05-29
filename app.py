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
from html import escape

import gradio as gr

from rater import stats
from rater.prompts import AXES, AXIS_DESCRIPTIONS

ACCENT = "#7c3aed"  # purple

CSS = """
:root { --accent: %s; }
.gradio-container { max-width: 1120px !important; }
#hero { background: linear-gradient(135deg, var(--accent), #0f172a);
        color:#fff; border-radius:18px; padding:26px 30px; margin-bottom:6px; }
#hero h1 { margin:0 0 8px 0; font-size:1.75rem; font-weight:800; letter-spacing:-.01em; }
#hero p { margin:0; opacity:.93; font-size:1.02rem; line-height:1.5; max-width:780px; }
#hero .pill { display:inline-block; background:rgba(255,255,255,.16); border-radius:999px;
        padding:3px 11px; font-size:.74rem; font-weight:700; margin-bottom:12px; letter-spacing:.04em; }
.verdict { border-radius:12px; padding:14px 18px; font-size:1.08rem; font-weight:800; margin:2px 0 12px; }
.verdict.ok   { background:#dcfce7; color:#166534; border:1px solid #86efac; }
.verdict.flag { background:#fef3c7; color:#92400e; border:1px solid #fcd34d; }
.kappa { border-radius:12px; padding:16px 20px; margin:2px 0 12px; }
.kappa b { font-size:1.5rem; }
table.qc { width:100%%; border-collapse:collapse; margin:8px 0; font-size:.92rem; }
table.qc th { text-align:left; padding:7px 10px; border-bottom:2px solid var(--accent); font-weight:700; }
table.qc td { padding:7px 10px; border-bottom:1px solid rgba(128,128,128,.2); }
pre.json { background:rgba(128,128,128,.12); padding:10px 12px; border-radius:8px;
        font-size:.82rem; overflow-x:auto; }
.footer { margin-top:20px; padding-top:14px; border-top:1px solid rgba(128,128,128,.25);
        font-size:.88rem; text-align:center; opacity:.92; }
.footer a { text-decoration:none; font-weight:700; color:var(--accent); }
""" % ACCENT

FOOTER = """
<div class="footer">
🧰 Part of an AI evaluation &amp; QC toolkit by <b>Laela Zorana</b> &nbsp;·&nbsp;
🔍 <a href="https://huggingface.co/spaces/LaelaZ/ai-agent-scenario-qc">Scenario QC</a> &nbsp;·&nbsp;
⚖️ RLHF Rater &nbsp;·&nbsp;
📦 <a href="https://huggingface.co/spaces/LaelaZ/scorm-qa-validator">SCORM QA</a> &nbsp;·&nbsp;
<a href="https://github.com/LaelaZorana/rlhf-pairwise-rater">Source on GitHub</a>
</div>
"""


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
    rating = {
        "id": "demo", "preference": preference, "confidence": int(confidence),
        "scores_a": {"helpfulness": int(h_a), "harmlessness": int(harm_a),
                     "accuracy": int(acc_a), "instruction_following": int(if_a)},
        "scores_b": {"helpfulness": int(h_b), "harmlessness": int(harm_b),
                     "accuracy": int(acc_b), "instruction_following": int(if_b)},
    }
    summary = stats.summarize([rating])
    flagged = "demo" in summary.get("self_consistency_flags", [])

    if flagged:
        banner = (f'<div class="verdict flag">⚠️ Self-consistency flag — you preferred '
                  f'<b>{preference}</b>, but the other response scored higher on <i>every</i> '
                  f'axis. This is exactly the silent rating error the tool catches.</div>')
    else:
        banner = ('<div class="verdict ok">✅ Consistent — your preference '
                  f'(<b>{preference}</b>, confidence {int(confidence)}/5) lines up with your axis scores.</div>')
    body = f'<pre class="json">{escape(json.dumps(rating, indent=2))}</pre>'
    return banner + body


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
        return f'<div class="verdict flag">❌ Invalid JSONL — {escape(str(exc))}</div>'

    result = stats.agreement_between(r1, r2)
    if not result.get("common_cases"):
        return '<div class="verdict flag">No overlapping case IDs between the two raters.</div>'

    kappa = result["kappa"]
    if kappa is None:
        interp, bg, fg = "", "#e5e7eb", "#111827"
    elif kappa >= 0.8:
        interp, bg, fg = "almost perfect agreement", "#dcfce7", "#166534"
    elif kappa >= 0.6:
        interp, bg, fg = "substantial agreement", "#dcfce7", "#166534"
    elif kappa >= 0.4:
        interp, bg, fg = "moderate agreement", "#fef3c7", "#92400e"
    elif kappa >= 0.2:
        interp, bg, fg = "fair agreement", "#fef3c7", "#92400e"
    else:
        interp, bg, fg = ("poor / near-chance — the rubric may be ambiguous or a rater has drifted",
                          "#fee2e2", "#991b1b")

    out = [f'<div class="kappa" style="background:{bg};color:{fg};">'
           f"Cohen's κ = <b>{kappa}</b> &nbsp; {interp}<br>"
           f'<span style="font-size:.9rem;">compared {result["common_cases"]} overlapping cases</span></div>']
    disagreements = result.get("disagreements", [])
    if disagreements:
        out.append('<table class="qc"><tr><th>Case</th><th>Rater 1</th><th>Rater 2</th></tr>')
        for cid, p1, p2 in disagreements:
            out.append(f"<tr><td>{escape(str(cid))}</td><td>{escape(str(p1))}</td>"
                       f"<td>{escape(str(p2))}</td></tr>")
        out.append("</table>")
    else:
        out.append("<p>No disagreements on the overlapping cases.</p>")
    return "\n".join(out)


theme = gr.themes.Soft(primary_hue="purple", neutral_hue="slate",
                       font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"])

with gr.Blocks(title="RLHF Pairwise Response Rater", theme=theme, css=CSS) as demo:
    gr.HTML(
        '<div id="hero"><span class="pill">RLHF / PREFERENCE DATA</span>'
        "<h1>⚖️ RLHF Pairwise Response Rater</h1>"
        "<p>The workflow behind preference data for RLHF — rate two model responses on four axes, "
        "pick a winner, and the tool checks your work. It catches <b>self-consistency errors</b> "
        "(you picked A but scored B higher everywhere) and measures <b>inter-rater agreement</b> "
        "with Cohen's kappa, so you can tell whether two people apply the same standard.</p></div>"
    )

    with gr.Tab("Rate a pair"):
        case_dd = gr.Dropdown(choices=CASE_LABELS, label="Load an example case",
                              value=CASE_LABELS[0] if CASE_LABELS else None)
        prompt_box = gr.Textbox(label="Prompt", lines=2)
        with gr.Row():
            a_box = gr.Textbox(label="🅰 Response A", lines=6)
            b_box = gr.Textbox(label="🅱 Response B", lines=6)

        gr.Markdown("**Score each response 1–5 on every axis** — "
                    + " · ".join(f"*{a}*: {AXIS_DESCRIPTIONS[a]}" for a in AXES))
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🅰 Response A")
                h_a = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_a = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_a = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_a = gr.Slider(1, 5, value=3, step=1, label="instruction_following")
            with gr.Column():
                gr.Markdown("### 🅱 Response B")
                h_b = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_b = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_b = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_b = gr.Slider(1, 5, value=3, step=1, label="instruction_following")

        with gr.Row():
            preference = gr.Radio(["A", "B", "TIE"], value="A", label="Overall preference")
            confidence = gr.Slider(1, 5, value=3, step=1, label="Confidence")

        rate_btn = gr.Button("Check my rating ▶", variant="primary", size="lg")
        rate_out = gr.HTML()

        case_dd.change(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])
        rate_btn.click(
            rate,
            inputs=[prompt_box, a_box, b_box, h_a, h_b, harm_a, harm_b,
                    acc_a, acc_b, if_a, if_b, preference, confidence],
            outputs=rate_out,
        )

    with gr.Tab("Inter-rater agreement (Cohen's κ)"):
        gr.Markdown(
            "Paste each rater's ratings as JSONL (one object per line, each with an `id` and a "
            "`preference` of `A` / `B` / `TIE`). The tool matches on shared case IDs and computes κ."
        )
        with gr.Row():
            r1_box = gr.Textbox(label="Rater 1 (JSONL)", value=KAPPA_EXAMPLE_1, lines=8)
            r2_box = gr.Textbox(label="Rater 2 (JSONL)", value=KAPPA_EXAMPLE_2, lines=8)
        kappa_btn = gr.Button("Compute agreement ▶", variant="primary", size="lg")
        kappa_out = gr.HTML()
        kappa_btn.click(agreement, inputs=[r1_box, r2_box], outputs=kappa_out)

    gr.HTML(FOOTER)
    gr.Markdown("*Runs the actual package (`rater/stats.py`) — the same code the pytest suite covers.*")

    demo.load(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])


if __name__ == "__main__":
    demo.launch()
