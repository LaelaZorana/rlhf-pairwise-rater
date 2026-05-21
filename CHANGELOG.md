# Changelog

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
