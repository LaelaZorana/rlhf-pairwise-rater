"""rlhf-pairwise-rater.

Pairwise rating of model responses for RLHF and preference-data work: score two
responses on four axes, pick a winner, then check the work two ways most rating
forms skip - a self-consistency flag and Cohen's kappa inter-rater agreement.

The public API is re-exported here so you can write:

    from rater import read_cases, summarize, cohens_kappa, agreement_between
"""
from __future__ import annotations

from .cases import append_rating, read_cases, read_ratings
from .prompts import AXES, AXIS_DESCRIPTIONS, rate_case
from .stats import agreement_between, cohens_kappa, summarize

__version__ = "0.3.0"

__all__ = [
    # data in / out
    "read_cases",
    "read_ratings",
    "append_rating",
    # rating
    "rate_case",
    "AXES",
    "AXIS_DESCRIPTIONS",
    # stats
    "summarize",
    "cohens_kappa",
    "agreement_between",
    "__version__",
]
