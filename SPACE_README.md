---
title: RLHF Pairwise Response Rater
emoji: ⚖️
colorFrom: purple
colorTo: pink
sdk: gradio
app_file: app.py
pinned: false
license: mit
---

# RLHF Pairwise Response Rater

The workflow behind preference data for RLHF — rate two model responses on four axes
(helpfulness, harmlessness, accuracy, instruction-following), pick a winner, and the
tool checks your work two ways most rating forms don't:

- **Self-consistency check** — flags when you pick a winner but score the loser higher
  on *every* axis (a real, common rater mistake).
- **Inter-rater agreement** — Cohen's kappa between two raters, so you can tell whether
  two people are actually applying the same standard or quietly drifting apart.

This Space runs the actual package (`rater/stats.py`) — the same code covered by the
project's pytest suite.

**Source & full docs:** https://github.com/LaelaZorana/rlhf-pairwise-rater
