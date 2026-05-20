"""CLI: rate / summary / agreement."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import cases as cases_mod
from . import prompts as prompts_mod
from . import stats as stats_mod
from .prompts import AXES


def cmd_rate(args) -> int:
    out = Path(args.out)
    already_rated_ids: set = set()
    if out.exists():
        already_rated_ids = {r["id"] for r in cases_mod.read_ratings(out)}
        print(f"Resuming — {len(already_rated_ids)} cases already rated in {out}")

    n = 0
    try:
        for case in cases_mod.read_cases(args.cases):
            if case.get("id") in already_rated_ids:
                continue
            rating = prompts_mod.rate_case(case, rater=args.rater)
            cases_mod.append_rating(out, rating)
            n += 1
    except KeyboardInterrupt:
        print(f"\nStopped. Rated {n} new case(s) this session.")
        return 0

    print(f"\nDone. Rated {n} new case(s) → {out}")
    return 0


def cmd_summary(args) -> int:
    ratings = cases_mod.read_ratings(args.ratings)
    s = stats_mod.summarize(ratings)
    print(f"\n=== Ratings summary: {args.ratings} ===")
    print(f"Total cases:       {s['total']}")
    if s["total"] == 0:
        return 0
    pc = s["preference_counts"]
    print(f"Preference split:  A={pc.get('A',0)}  B={pc.get('B',0)}  TIE={pc.get('TIE',0)}")
    print(f"Mean confidence:   {s['mean_confidence']} / 5")
    print(f"\nPer-axis average score")
    print(f"{'':<22}  A    B")
    for ax in AXES:
        print(f"{ax:<22} {s['axis_means_a'][ax]:>3}   {s['axis_means_b'][ax]:>3}")
    print(f"\nSelf-consistency flags: {len(s['self_consistency_flags'])} case(s)")
    for cid in s["self_consistency_flags"]:
        print(f"  - {cid}")
    return 0


def cmd_agreement(args) -> int:
    r1 = cases_mod.read_ratings(args.ratings_1)
    r2 = cases_mod.read_ratings(args.ratings_2)
    a = stats_mod.agreement_between(r1, r2)
    print(json.dumps(a, indent=2))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="rater")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("rate", help="Interactively rate a JSONL of comparison cases")
    pr.add_argument("cases", type=Path)
    pr.add_argument("--rater", required=True, help="Your handle/initials")
    pr.add_argument("--out", required=True, type=Path)

    ps = sub.add_parser("summary", help="Print summary stats over a ratings file")
    ps.add_argument("ratings", type=Path)

    pa = sub.add_parser("agreement", help="Cohen's kappa between two raters")
    pa.add_argument("ratings_1", type=Path)
    pa.add_argument("ratings_2", type=Path)

    args = p.parse_args(argv)
    if args.cmd == "rate":
        return cmd_rate(args)
    if args.cmd == "summary":
        return cmd_summary(args)
    if args.cmd == "agreement":
        return cmd_agreement(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
