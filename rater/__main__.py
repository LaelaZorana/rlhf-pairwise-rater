import argparse, sys
from pathlib import Path
from . import cases as cases_mod, prompts as prompts_mod, stats as stats_mod


def cmd_rate(args):
    n = 0
    try:
        for case in cases_mod.read_cases(args.cases):
            r = prompts_mod.rate_case(case, args.rater)
            cases_mod.append_rating(args.out, r)
            n += 1
    except KeyboardInterrupt:
        pass
    print(f"\nRated {n}.")
    return 0


def cmd_summary(args):
    import json
    print(json.dumps(stats_mod.summarize(cases_mod.read_ratings(args.ratings)), indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="rater")
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("rate")
    pr.add_argument("cases", type=Path); pr.add_argument("--rater", required=True); pr.add_argument("--out", required=True, type=Path)
    ps = sub.add_parser("summary"); ps.add_argument("ratings", type=Path)
    args = p.parse_args(argv)
    return cmd_rate(args) if args.cmd == "rate" else cmd_summary(args)


if __name__ == "__main__":
    sys.exit(main())
