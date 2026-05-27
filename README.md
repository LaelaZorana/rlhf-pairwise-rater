# rlhf-pairwise-rater

A small CLI for **pairwise rating of AI model responses** — the kind of task that shows up everywhere in RLHF / preference-data pipelines: you get a prompt and two candidate responses (call them A and B), you rate them on a few axes (helpfulness, harmlessness, accuracy, instruction-following), and pick a winner.

I built this to practice the rating workflow itself, and to have a structured way of *recording* my own ratings as I went through evaluation tasks — so I could review my rubric application later, look for inconsistencies in my own judgments, and produce a clean dataset that another reviewer could audit.

## What it does

Given a JSONL file of comparison cases like:

```json
{"id": "001", "prompt": "Explain photosynthesis to a 10-year-old.", "response_a": "...", "response_b": "..."}
```

it walks you through each case in the terminal and asks you to score both responses on four axes (1–5):

- **Helpfulness** — does it actually answer the prompt?
- **Harmlessness** — is anything in it unsafe, misleading, or biased?
- **Accuracy** — is the factual content correct?
- **Instruction-following** — did it do *what was asked*, in the right format/length/tone?

It then asks for an overall preference (A / B / TIE) and an optional free-text reason.

Output is a JSONL of structured ratings:

```json
{
  "id": "001",
  "rater": "laela",
  "scores_a": {"helpfulness": 4, "harmlessness": 5, "accuracy": 4, "instruction_following": 5},
  "scores_b": {"helpfulness": 3, "harmlessness": 5, "accuracy": 5, "instruction_following": 3},
  "preference": "A",
  "confidence": 4,
  "reason": "B is more accurate but rambles; A hits the 10-year-old framing and stays concise."
}
```

## Why bother

Two things kept tripping me up when I was doing rating tasks on training platforms:

1. **My own consistency drift.** After 20 cases I'd forget exactly how I was weighting "harmlessness" vs "helpfulness" — and my ratings would slowly drift. Recording the per-axis scores forces explicitness.
2. **Rationale recall.** When a reviewer asks "why did you prefer A here?" three days later, you can't remember. Storing a one-line reason inline fixes that.

So this is partly a practice tool, partly a personal QA dataset generator.

## Install & run

```bash
pip install -r requirements.txt
python -m rater rate examples/sample_cases.jsonl --rater laela --out my_ratings.jsonl
```

Other commands:

```bash
# Show summary stats over a ratings file
python -m rater summary my_ratings.jsonl

# Check inter-rater agreement between two raters' files
python -m rater agreement laela.jsonl alex.jsonl
```

## Summary report example

```
=== Ratings summary: my_ratings.jsonl ===
Total cases:       12
Preference split:  A=6  B=4  TIE=2
Mean confidence:   3.8 / 5

Per-axis average score
                 A     B
helpfulness     4.1   3.5
harmlessness    4.9   4.8
accuracy        3.9   4.2
instruction     4.3   3.4

Self-consistency flag: 0 cases where the preference and per-axis scores disagreed.
```

## Tests

```bash
pytest -v
```

Covers JSONL round-trip, the agreement computation (Cohen's kappa on the preference column), and the self-consistency check (catches cases where you said A wins overall but scored B higher on every axis — a real thing that has happened to me).

## Layout

```
rater/
  __main__.py          CLI
  cases.py             JSONL reading / writing
  prompts.py           the rating prompts I use
  stats.py             summary + agreement
tests/
examples/
  sample_cases.jsonl   3 toy cases for kicking the tires
```

## License

MIT.

---

**Links:** [GitHub](https://github.com/LaelaZorana) · [HuggingFace](https://huggingface.co/LaelaZ) · [Kaggle](https://www.kaggle.com/laelazorana)
