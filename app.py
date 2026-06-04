"""
Gradio demo for the RLHF Pairwise Response Rater.

Two things this tool does that a plain rating form does not:
  1. Self-consistency check: flags when you pick a winner but score the loser
     higher on every axis (a real, common rater mistake).
  2. Inter-rater agreement: Cohen's kappa between two raters, so you can see
     whether two people are actually applying the same standard.

Both run the real package code in rater/stats.py, the same functions covered
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


# Friendly axis labels for the paired bars (kept short and plain).
AXIS_SHORT = {
    "helpfulness": "helpful",
    "harmlessness": "harmless",
    "accuracy": "accurate",
    "instruction_following": "follows ask",
}


def _response_card(name: str, text: str, is_winner: bool, pref: str) -> str:
    """One side of the pair. The preferred side glows and wears a badge."""
    safe = escape(text.strip()) if text and text.strip() else "<i>empty</i>"
    cls = "rl-card rl-resp rl-win" if is_winner else "rl-card rl-resp"
    badge = ""
    if is_winner and pref != "TIE":
        badge = '<span class="rl-badge">preferred</span>'
    elif pref == "TIE":
        badge = '<span class="rl-badge rl-badge-tie">tie</span>'
    return (
        f'<div class="{cls}">'
        f'<div class="rl-resp-head"><span class="rl-resp-name">Response {name}</span>{badge}</div>'
        f'<div class="rl-resp-text">{safe}</div>'
        f"</div>"
    )


def _paired_bars(scores_a: dict, scores_b: dict) -> str:
    """Small paired bars so you can see A vs B per axis at a glance."""
    rows = []
    for axis in AXES:
        a = int(scores_a[axis])
        b = int(scores_b[axis])
        short = AXIS_SHORT.get(axis, axis)
        rows.append(
            f'<div class="rl-bar-row">'
            f'<div class="rl-bar-name">{escape(short)}</div>'
            f'<div class="rl-bar-pair">'
            f'<div class="rl-bar-side rl-bar-a">'
            f'<div class="rl-bar-fill rl-fill-a" style="width:{a/5*100:.0f}%"></div>'
            f'<span class="rl-bar-val">A {a}</span></div>'
            f'<div class="rl-bar-side rl-bar-b">'
            f'<div class="rl-bar-fill rl-fill-b" style="width:{b/5*100:.0f}%"></div>'
            f'<span class="rl-bar-val">B {b}</span></div>'
            f"</div></div>"
        )
    return f'<div class="rl-card rl-bars">{"".join(rows)}</div>'


def rate(prompt, resp_a, resp_b,
         h_a, h_b, harm_a, harm_b, acc_a, acc_b, if_a, if_b,
         preference, confidence):
    scores_a = {"helpfulness": int(h_a), "harmlessness": int(harm_a),
                "accuracy": int(acc_a), "instruction_following": int(if_a)}
    scores_b = {"helpfulness": int(h_b), "harmlessness": int(harm_b),
                "accuracy": int(acc_b), "instruction_following": int(if_b)}
    rating = {
        "id": "demo", "preference": preference, "confidence": int(confidence),
        "scores_a": scores_a, "scores_b": scores_b,
    }
    summary = stats.summarize([rating])
    flagged = "demo" in summary.get("self_consistency_flags", [])

    if flagged:
        banner = (
            '<div class="rl-verdict rl-flag">'
            '<span class="rl-verdict-icon">!</span>'
            '<div><div class="rl-verdict-title">Self-consistency flag</div>'
            f'<div class="rl-verdict-sub">You preferred <b>{escape(str(preference))}</b>, '
            'but the other response scored higher on every axis. '
            'This is the silent rating error the tool catches.</div></div></div>'
        )
    else:
        banner = (
            '<div class="rl-verdict rl-ok">'
            '<span class="rl-verdict-icon">OK</span>'
            '<div><div class="rl-verdict-title">Consistent</div>'
            f'<div class="rl-verdict-sub">Your preference (<b>{escape(str(preference))}</b>, '
            f'confidence {int(confidence)} of 5) lines up with your axis scores.</div></div></div>'
        )

    pref = str(preference)
    cards = (
        '<div class="rl-pair">'
        + _response_card("A", resp_a, pref == "A", pref)
        + _response_card("B", resp_b, pref == "B", pref)
        + "</div>"
    )
    bars = _paired_bars(scores_a, scores_b)
    return f'<div class="rl-result">{banner}{cards}{bars}</div>'


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


def _flag_banner(msg: str) -> str:
    return (
        '<div class="rl-result"><div class="rl-verdict rl-flag">'
        '<span class="rl-verdict-icon">!</span>'
        f'<div><div class="rl-verdict-title">{escape(msg)}</div></div></div></div>'
    )


def agreement(rater1_text, rater2_text):
    try:
        r1 = _parse_jsonl(rater1_text)
        r2 = _parse_jsonl(rater2_text)
    except json.JSONDecodeError as exc:
        return _flag_banner("Invalid JSONL: " + str(exc))

    result = stats.agreement_between(r1, r2)
    if not result.get("common_cases"):
        return _flag_banner("No overlapping case IDs between the two raters.")

    kappa = result["kappa"]
    if kappa is None:
        interp, accent, soft = "", "#6b7280", "#e5e7eb"
    elif kappa >= 0.8:
        interp, accent, soft = "almost perfect agreement", "#166534", "#dcfce7"
    elif kappa >= 0.6:
        interp, accent, soft = "substantial agreement", "#166534", "#dcfce7"
    elif kappa >= 0.4:
        interp, accent, soft = "moderate agreement", "#92400e", "#fef3c7"
    elif kappa >= 0.2:
        interp, accent, soft = "fair agreement", "#92400e", "#fef3c7"
    else:
        interp, accent, soft = (
            "poor or near chance, the rubric may be ambiguous or a rater has drifted",
            "#991b1b", "#fee2e2",
        )

    kappa_txt = "n/a" if kappa is None else f"{kappa}"
    # meter fill maps kappa from -1..1 onto 0..100
    fill = 0 if kappa is None else max(0.0, min(1.0, (kappa + 1) / 2)) * 100

    out = [
        '<div class="rl-result">',
        '<div class="rl-card rl-kappa" style="--rl-k:%s">' % accent,
        '<div class="rl-kappa-top">'
        '<div class="rl-kappa-label">Cohen\'s kappa</div>'
        f'<div class="rl-kappa-num" style="color:{accent}">{escape(kappa_txt)}</div>'
        f'<div class="rl-kappa-interp" style="background:{soft};color:{accent}">'
        f'{escape(interp) if interp else "no shared cases to score"}</div>'
        "</div>",
        '<div class="rl-meter"><div class="rl-meter-fill" '
        f'style="width:{fill:.0f}%;background:{accent}"></div></div>',
        '<div class="rl-kappa-foot">compared '
        f'{int(result["common_cases"])} overlapping cases</div>',
        "</div>",
    ]

    disagreements = result.get("disagreements", [])
    if disagreements:
        items = []
        for cid, p1, p2 in disagreements:
            items.append(
                '<div class="rl-dis-row">'
                f'<span class="rl-dis-id">{escape(str(cid))}</span>'
                f'<span class="rl-dis-p">Rater 1: <b>{escape(str(p1))}</b></span>'
                f'<span class="rl-dis-p">Rater 2: <b>{escape(str(p2))}</b></span>'
                "</div>"
            )
        out.append(
            '<div class="rl-card rl-dis"><div class="rl-dis-head">'
            f'Where they disagreed ({len(disagreements)})</div>'
            + "".join(items) + "</div>"
        )
    else:
        out.append(
            '<div class="rl-card rl-dis"><div class="rl-dis-head">No disagreements</div>'
            '<div class="rl-dis-empty">Both raters agreed on every overlapping case.</div></div>'
        )
    out.append("</div>")
    return "\n".join(out)


CSS = """
:root {
  --rl-bg1:#faf5ff; --rl-bg2:#eef2ff; --rl-ink:#1e1b2e; --rl-muted:#6b6880;
  --rl-card:#ffffff; --rl-line:rgba(20,16,40,.08); --rl-accent:#7c3aed;
  --rl-font:'Plus Jakarta Sans','Inter',system-ui,sans-serif;
}

/* Light lock: HF Spaces default to dark mode, but this UI is designed light.
   Override Gradio's dark theme variables so it renders light everywhere. */
:root, .dark, gradio-app.dark {
  color-scheme: light !important;
  --body-background-fill:#ffffff !important;
  --background-fill-primary:#ffffff !important;
  --background-fill-secondary:#f6f6fb !important;
  --block-background-fill:#ffffff !important;
  --block-label-background-fill:#ffffff !important;
  --input-background-fill:#ffffff !important;
  --border-color-primary:rgba(20,16,40,.12) !important;
  --body-text-color:#16131f !important;
  --body-text-color-subdued:#6b6880 !important;
  --block-title-text-color:#16131f !important;
  --block-info-text-color:#6b6880 !important;
}
html, body, gradio-app, .dark { background:#ffffff !important; }

.gradio-container { max-width: 980px !important; background:
  radial-gradient(1200px 500px at 12% -10%, var(--rl-bg1), transparent 60%),
  radial-gradient(1000px 500px at 112% 8%, var(--rl-bg2), transparent 55%) !important; }
.gradio-container, .gradio-container * { font-family: var(--rl-font); }

/* Header */
#rl-head { text-align:center; padding: 18px 8px 6px; }
#rl-head .rl-pill { display:inline-block; background:#1e1b2e; color:#fff; border-radius:999px;
  padding:5px 13px; font-size:.7rem; font-weight:700; letter-spacing:.08em; margin-bottom:14px; }
#rl-head h1 { margin:0; font-size:2.0rem; font-weight:800; letter-spacing:-.02em; color:var(--rl-ink);
  background:linear-gradient(90deg,#7c3aed,#a855f7,#6366f1); -webkit-background-clip:text;
  background-clip:text; -webkit-text-fill-color:transparent; }
#rl-head p { margin:10px auto 0; max-width:640px; color:var(--rl-muted); font-size:1.0rem; line-height:1.55; }

/* Buttons + inputs */
.rl-go { border-radius:14px !important; font-weight:800 !important; font-size:1rem !important;
  background:linear-gradient(135deg,#7c3aed,#6366f1) !important; border:none !important; color:#fff !important;
  box-shadow:0 10px 26px rgba(124,58,237,.32) !important; transition:transform .12s ease, box-shadow .12s ease !important; }
.rl-go:hover { transform:translateY(-1px); box-shadow:0 14px 32px rgba(124,58,237,.42) !important; }

/* Result wrapper animation */
.rl-result { animation: rl-fade .35s ease both; }
@keyframes rl-fade { from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }

/* Card system */
.rl-card { background:var(--rl-card); border:1px solid var(--rl-line); border-radius:18px;
  box-shadow:0 12px 32px rgba(30,27,46,.06); padding:18px 20px; margin-top:14px; }

/* Verdict banner */
.rl-verdict { display:flex; gap:14px; align-items:flex-start; border-radius:18px;
  padding:16px 20px; animation: rl-grow .4s cubic-bezier(.2,.8,.2,1) both; }
@keyframes rl-grow { from{opacity:0; transform:scale(.98)} to{opacity:1; transform:scale(1)} }
.rl-verdict-icon { flex-shrink:0; width:34px; height:34px; border-radius:50%; display:grid;
  place-items:center; font-weight:800; font-size:.9rem; color:#fff; }
.rl-verdict-title { font-weight:800; font-size:1.08rem; }
.rl-verdict-sub { font-size:.94rem; margin-top:3px; line-height:1.5; }
.rl-ok { background:#dcfce7; border:1px solid #86efac; color:#166534; }
.rl-ok .rl-verdict-icon { background:#16a34a; }
.rl-flag { background:#fef3c7; border:1px solid #fcd34d; color:#92400e; }
.rl-flag .rl-verdict-icon { background:#d97706; }

/* Paired response cards */
.rl-pair { display:flex; gap:14px; }
.rl-pair .rl-resp { flex:1; }
.rl-resp { transition:box-shadow .2s ease, border-color .2s ease; }
.rl-resp-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }
.rl-resp-name { font-weight:800; color:var(--rl-ink); font-size:1.0rem; }
.rl-resp-text { color:var(--rl-ink); font-size:.92rem; line-height:1.5; white-space:pre-wrap;
  max-height:220px; overflow:auto; }
.rl-win { border:1px solid #16a34a; box-shadow:0 14px 36px rgba(22,163,74,.20); }
.rl-badge { background:#16a34a; color:#fff; border-radius:999px; padding:3px 11px;
  font-size:.7rem; font-weight:800; letter-spacing:.04em; text-transform:uppercase; }
.rl-badge-tie { background:#6b7280; }

/* Paired axis bars */
.rl-bar-row { display:flex; align-items:center; gap:12px; padding:6px 0; }
.rl-bar-name { width:96px; font-weight:700; color:var(--rl-ink); font-size:.86rem; }
.rl-bar-pair { flex:1; display:flex; flex-direction:column; gap:6px; }
.rl-bar-side { position:relative; height:18px; border-radius:999px; background:#f1eef9; overflow:hidden; }
.rl-bar-fill { height:100%; border-radius:999px; transform-origin:left;
  animation: rl-fill .6s cubic-bezier(.2,.8,.2,1) both; }
@keyframes rl-fill { from{transform:scaleX(0)} to{transform:scaleX(1)} }
.rl-fill-a { background:#7c3aed; }
.rl-fill-b { background:#6366f1; }
.rl-bar-val { position:absolute; right:8px; top:0; line-height:18px; font-size:.72rem;
  font-weight:800; color:#1e1b2e; }

/* Kappa meter card */
.rl-kappa-top { display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
.rl-kappa-label { font-weight:700; color:var(--rl-muted); font-size:.9rem; }
.rl-kappa-num { font-size:2.6rem; font-weight:800; letter-spacing:-.02em; line-height:1;
  font-variant-numeric:tabular-nums; }
.rl-kappa-interp { border-radius:999px; padding:4px 12px; font-size:.82rem; font-weight:700; }
.rl-meter { margin-top:14px; height:14px; border-radius:999px; background:#f1eef9; overflow:hidden; }
.rl-meter-fill { height:100%; border-radius:999px; transform-origin:left;
  animation: rl-fill .7s cubic-bezier(.2,.8,.2,1) both; }
.rl-kappa-foot { margin-top:8px; color:var(--rl-muted); font-size:.86rem; }

/* Disagreement list */
.rl-dis-head { font-weight:800; color:var(--rl-ink); font-size:1.0rem; margin-bottom:10px; }
.rl-dis-row { display:flex; gap:16px; align-items:center; padding:8px 0;
  border-top:1px solid var(--rl-line); font-size:.9rem; color:var(--rl-ink); }
.rl-dis-row:first-of-type { border-top:none; }
.rl-dis-id { font-weight:800; color:var(--rl-accent); width:64px; }
.rl-dis-p { color:var(--rl-muted); }
.rl-dis-empty { color:var(--rl-muted); font-size:.92rem; }

/* Footer */
.rl-footer { margin-top:22px; padding-top:16px; border-top:1px solid var(--rl-line);
  text-align:center; font-size:.88rem; color:var(--rl-muted); line-height:1.9; }
.rl-footer a { text-decoration:none; font-weight:700; color:var(--rl-accent); }
.rl-meta { text-align:center; color:var(--rl-muted); font-size:.82rem; margin-top:10px; }
"""


FOOTER = """
<div class="rl-footer">
Part of an AI evaluation and QC toolkit by <b>Laela Zorana</b><br>
<a href="https://huggingface.co/spaces/LaelaZ/ai-agent-scenario-qc">Scenario QC</a> &middot;
RLHF Rater &middot;
<a href="https://huggingface.co/spaces/LaelaZ/scorm-qa-validator">SCORM QA</a> &middot;
<a href="https://github.com/LaelaZorana/rlhf-pairwise-rater">Source on GitHub</a>
</div>
"""


theme = gr.themes.Soft(
    primary_hue="violet", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), gr.themes.GoogleFont("Inter"),
          "system-ui", "sans-serif"],
)

with gr.Blocks(title="RLHF Pairwise Response Rater", theme=theme, css=CSS) as demo:
    gr.HTML(
        '<div id="rl-head"><span class="rl-pill">RLHF · PREFERENCE DATA</span>'
        "<h1>RLHF Pairwise Response Rater</h1>"
        "<p>This is the workflow behind preference data for RLHF. Rate two model responses "
        "on four axes, pick a winner, and the tool checks your work. It catches "
        "<b>self-consistency errors</b>, like picking A but scoring B higher everywhere, and it "
        "measures <b>inter-rater agreement</b> with Cohen's kappa so you can tell whether two "
        "people apply the same standard.</p></div>"
    )

    with gr.Tab("Rate a pair"):
        case_dd = gr.Dropdown(choices=CASE_LABELS, label="Load an example case",
                              value=CASE_LABELS[0] if CASE_LABELS else None)
        prompt_box = gr.Textbox(label="Prompt", lines=2)
        with gr.Row():
            a_box = gr.Textbox(label="Response A", lines=6)
            b_box = gr.Textbox(label="Response B", lines=6)

        gr.Markdown("**Score each response 1 to 5 on every axis.** "
                    + " · ".join(f"*{a}*: {AXIS_DESCRIPTIONS[a]}" for a in AXES))
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Response A")
                h_a = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_a = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_a = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_a = gr.Slider(1, 5, value=3, step=1, label="instruction_following")
            with gr.Column():
                gr.Markdown("### Response B")
                h_b = gr.Slider(1, 5, value=3, step=1, label="helpfulness")
                harm_b = gr.Slider(1, 5, value=3, step=1, label="harmlessness")
                acc_b = gr.Slider(1, 5, value=3, step=1, label="accuracy")
                if_b = gr.Slider(1, 5, value=3, step=1, label="instruction_following")

        with gr.Row():
            preference = gr.Radio(["A", "B", "TIE"], value="A", label="Overall preference")
            confidence = gr.Slider(1, 5, value=3, step=1, label="Confidence")

        rate_btn = gr.Button("Check my rating", variant="primary", elem_classes="rl-go")
        rate_out = gr.HTML()

        case_dd.change(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])
        rate_btn.click(
            rate,
            inputs=[prompt_box, a_box, b_box, h_a, h_b, harm_a, harm_b,
                    acc_a, acc_b, if_a, if_b, preference, confidence],
            outputs=rate_out,
        )

    with gr.Tab("Inter-rater agreement (Cohen's kappa)"):
        gr.Markdown(
            "Paste each rater's ratings as JSONL, one object per line, each with an `id` and a "
            "`preference` of `A`, `B`, or `TIE`. The tool matches on shared case IDs and computes kappa."
        )
        with gr.Row():
            r1_box = gr.Textbox(label="Rater 1 (JSONL)", value=KAPPA_EXAMPLE_1, lines=8)
            r2_box = gr.Textbox(label="Rater 2 (JSONL)", value=KAPPA_EXAMPLE_2, lines=8)
        kappa_btn = gr.Button("Compute agreement", variant="primary", elem_classes="rl-go")
        kappa_out = gr.HTML()
        kappa_btn.click(agreement, inputs=[r1_box, r2_box], outputs=kappa_out)

    gr.HTML(FOOTER)
    gr.HTML('<div class="rl-meta">Runs the actual package (rater/stats.py), the same code '
            'the pytest suite covers.</div>')

    demo.load(pick_case, inputs=case_dd, outputs=[prompt_box, a_box, b_box])


if __name__ == "__main__":
    demo.launch()
