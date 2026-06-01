# rlhf-pairwise-rater

[![CI](https://github.com/LaelaZorana/rlhf-pairwise-rater/actions/workflows/ci.yml/badge.svg)](https://github.com/LaelaZorana/rlhf-pairwise-rater/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/rlhf-pairwise-rater.svg)](https://pypi.org/project/rlhf-pairwise-rater/)
[![Python](https://img.shields.io/pypi/pyversions/rlhf-pairwise-rater.svg)](https://pypi.org/project/rlhf-pairwise-rater/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pairwise rating of model responses for RLHF and preference-data work. You get a prompt and two candidate responses (call them A and B), you score each on four axes (helpfulness, harmlessness, accuracy, instruction-following), and you pick a winner. The library records every rating as structured data and then checks your work two ways most rating forms skip.

**Live demo:** [try it on Hugging Face Spaces](https://huggingface.co/spaces/LaelaZ/rlhf-pairwise-rater). Rate a pair and watch the self-consistency check and Cohen's kappa update live.

## The two checks that make this more than a form

1. **Self-consistency flag.** If you pick A as the winner but scored B higher on *every* axis, that gets flagged. It is a real mistake that happens when you rate fast, and nothing on a normal rating form catches it.
2. **Inter-rater agreement.** Cohen's kappa between two raters over the same cases, so you can tell whether two people are actually applying the same standard or quietly drifting apart. Kappa corrects for the agreement you would get by chance, which raw percent-agreement does not.

## Install

```bash
pip install rlhf-pairwise-rater
```

That gives you both the `rater` Python package and the `rlhf-rater` command-line tool. The library core is pure standard library, so there are no runtime dependencies to pull in.

## Use it as a library

```python
from rater import summarize, cohens_kappa, agreement_between, read_ratings

# Summary stats over one rater's file (preference split, per-axis means,
# self-consistency flags).
ratings = read_ratings("laela.jsonl")
print(summarize(ratings))

# How well do two raters agree? Pass each rater's list of ratings.
report = agreement_between(read_ratings("laela.jsonl"), read_ratings("alex.jsonl"))
print(report)        # {'common_cases': 40, 'kappa': 0.71, 'disagreements': [...]}

# Or compute Cohen's kappa directly on any two aligned label sequences.
cohens_kappa(["A", "B", "A", "TIE"], ["A", "B", "TIE", "TIE"])   # -> 0.636
```

`summarize` returns, for a list of ratings: the total, the A/B/TIE preference split, mean confidence, per-axis mean scores for A and B, and the ids of any self-consistency flags.

## Use it from the command line

```bash
# Rate a JSONL of comparison cases, one at a time, in your terminal.
rlhf-rater rate examples/sample_cases.jsonl --rater laela --out laela.jsonl

# Print summary stats over a ratings file.
rlhf-rater summary laela.jsonl

# Cohen's kappa between two raters' files.
rlhf-rater agreement laela.jsonl alex.jsonl
```

Re-running `rate` on the same output file resumes where you left off and skips cases you already rated.

## Data format

Input is a JSONL file of comparison cases, one per line:

```json
{"id": "001", "prompt": "Explain photosynthesis to a 10-year-old.", "response_a": "...", "response_b": "..."}
```

Output is a JSONL file of structured ratings, one per line:

```json
{
  "id": "001",
  "rater": "laela",
  "scores_a": {"helpfulness": 4, "harmlessness": 5, "accuracy": 4, "instruction_following": 5},
  "scores_b": {"helpfulness": 3, "harmlessness": 5, "accuracy": 5, "instruction_following": 3},
  "preference": "A",
  "confidence": 4,
  "reason": "B is more accurate but rambles; A keeps the 10-year-old framing and stays concise."
}
```

The four axes:

- **Helpfulness.** Does it actually answer the prompt?
- **Harmlessness.** Is anything in it unsafe, misleading, or biased?
- **Accuracy.** Is the factual content correct?
- **Instruction-following.** Did it do what was asked, in the right format, length, and tone?

## Why I built it

Two things kept tripping me up on rating tasks. First, consistency drift: after twenty cases I would forget exactly how I was weighting harmlessness against helpfulness, and my ratings would slowly shift. Recording the per-axis scores forces it to be explicit. Second, rationale recall: when a reviewer asks "why did you prefer A here?" three days later, you cannot remember, so a one-line reason gets stored inline. The result is part practice tool, part personal QA dataset generator.

## Public API

| Import | What it does |
| --- | --- |
| `read_cases(path)` | Yield each comparison case from a JSONL file. |
| `read_ratings(path)` | Read a ratings JSONL file into a list. |
| `append_rating(path, rating)` | Append one rating dict to a JSONL file. |
| `rate_case(case, rater)` | Walk a single case interactively and return the rating dict. |
| `summarize(ratings)` | Preference split, per-axis means, confidence, self-consistency flags. |
| `cohens_kappa(labels_1, labels_2)` | Cohen's kappa over two aligned label sequences. |
| `agreement_between(ratings_1, ratings_2)` | Kappa plus the disagreement breakdown for two raters. |
| `AXES`, `AXIS_DESCRIPTIONS` | The four scoring axes and their definitions. |

## Development

```bash
git clone https://github.com/LaelaZorana/rlhf-pairwise-rater
cd rlhf-pairwise-rater
pip install -e ".[dev]"
pytest -v
```

Build the distribution artifacts:

```bash
pip install build
python -m build      # writes dist/*.whl and dist/*.tar.gz
```

The test suite covers the JSONL round-trip, the kappa computation, and the self-consistency check (it confirms a case where you said A wins but scored B higher on every axis gets flagged). CI runs the suite on Python 3.9 through 3.12.

## Layout

```
rater/
  __init__.py          public API
  __main__.py          the rlhf-rater command line
  cases.py             JSONL reading and writing
  prompts.py           the interactive rating flow and the four axes
  stats.py             summary, self-consistency, Cohen's kappa
tests/
examples/
  sample_cases.jsonl   3 toy cases for kicking the tires
app.py                 the Gradio demo that runs on Hugging Face Spaces
```

## License

MIT. See [LICENSE](LICENSE).

---

**Links:** [GitHub](https://github.com/LaelaZorana) · [Hugging Face](https://huggingface.co/LaelaZ) · [Kaggle](https://www.kaggle.com/laelazorana)
