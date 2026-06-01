# Changelog

## 0.3.0 - 2026-05-31

- Packaged for PyPI: added `pyproject.toml`, so the project installs with
  `pip install rlhf-pairwise-rater` instead of a manual clone.
- Public API: the key functions are now re-exported from the top level, so you
  can write `from rater import summarize, cohens_kappa, agreement_between`.
- Console entry point: the CLI is now available as the `rlhf-rater` command,
  alongside the existing `python -m rater`.
- Continuous integration: GitHub Actions runs the test suite on Python 3.9
  through 3.12 on every push and pull request.
- No runtime dependencies for the library core (pure standard library).

## 0.2.0 — 2026-05-21

- Added `agreement` subcommand (Cohen's kappa between two raters)
- Resume support: re-running `rate` skips cases already in the output file
- Added "self-consistency" check to the summary — flags ratings where the
  per-axis scores contradict the overall preference

## 0.1.1 — 2026-05-15

- Fix: `summarize()` divided by zero when ratings file was empty.
- Fix: confidence prompt accepted 0 (range was wrong).

## 0.1.0 — 2026-05-12

- First version. CLI with `rate` and `summary` commands.
- 4 axes: helpfulness, harmlessness, accuracy, instruction-following.
- JSONL in, JSONL out.
