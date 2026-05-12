# rlhf-pairwise-rater

A tiny CLI for pairwise rating of AI responses. WIP.

Plan:
- read a JSONL of (prompt, response_a, response_b)
- walk you through scoring each on a few axes (1-5)
- ask for preference (A/B/tie) + a one-line reason
- save the ratings as JSONL
