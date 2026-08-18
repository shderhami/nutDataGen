"""CLI for the intake pipeline.

    python -m intake search "chicken thigh" [--source mext]
    python -m intake report --spec data/intake/chicken_thigh_skinless.json
    python -m intake write  --spec ... --decisions ... [--commit]
"""
from __future__ import annotations

import argparse
import sys


def _cmd_search(args: argparse.Namespace) -> int:
    from intake.sources import registry

    for name, adapter in registry().items():
        if args.source and name != args.source:
            continue
        try:
            hits = adapter.search(args.query)
        except Exception as exc:  # noqa: BLE001 - report per-source, keep going
            print(f"== {name}: ERROR {exc}")
            continue
        print(f"== {name}: {len(hits)} hit(s)")
        for key, desc in hits[: args.limit]:
            print(f"   {key} | {desc}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from intake import extract
    from intake.compare import compare_all, verdict_counts
    from intake.report import write_artifacts
    from intake.spec import load_spec

    spec = load_spec(args.spec)
    extraction = extract.run(spec)
    comparisons, echo_verdicts = compare_all(extraction)
    report_path, decisions_path = write_artifacts(
        spec, extraction, comparisons, echo_verdicts)
    print(f"report:    {report_path}")
    print(f"decisions: {decisions_path}")
    print(f"verdicts:  {verdict_counts(comparisons)}")
    return 0


def _cmd_write(args: argparse.Namespace) -> int:
    from intake.spec import load_spec
    from intake.writer import apply, load_decisions

    spec = load_spec(args.spec)
    decisions, meta = load_decisions(args.decisions)
    apply(spec, decisions, commit=args.commit,
          signed_off_by=args.signed_off_by, meta=meta)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="intake", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="find a food key in each source")
    p.add_argument("query")
    p.add_argument("--source", help="limit to one adapter name")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(func=_cmd_search)

    p = sub.add_parser("report", help="extract + compare + write review artifacts")
    p.add_argument("--spec", required=True)
    p.set_defaults(func=_cmd_report)

    p = sub.add_parser("write", help="write reviewed decisions to the DB")
    p.add_argument("--spec", required=True)
    p.add_argument("--decisions", required=True)
    p.add_argument("--commit", action="store_true")
    p.add_argument("--signed-off-by", dest="signed_off_by",
                   help="required with --commit (cv_assign contract)")
    p.set_defaults(func=_cmd_write)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        from intake.writer import GateFailure

        if isinstance(exc, (GateFailure, KeyError)):
            # expected refusals (gates, bad spec keys) are operator messages,
            # not crashes — no traceback (round-3 live-write audit)
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        raise


if __name__ == "__main__":
    sys.exit(main())
