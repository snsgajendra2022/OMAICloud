"""argparse handlers for ``om-ai learn`` (not Typer — matches main CLI).

Background learning loop:
  Gaps → Scheduler → Teachers/Distill → SFT/DPO → Training Queue → OM Improvement
"""
from __future__ import annotations

import json


def learn_cmd(args) -> None:
    """Dispatch ``om-ai learn <sub>``."""
    from om_ai.core.learning import ImprovementCycle

    cycle = ImprovementCycle()
    sub = getattr(args, "learn_sub", None) or getattr(args, "sub", None)

    if sub == "start":
        result = cycle.start(
            max_items=int(getattr(args, "max_items", 5) or 5),
            topic=(getattr(args, "topic", None) or None),
            count=int(getattr(args, "count", 5) or 5),
            domain=str(getattr(args, "domain", "software") or "software"),
            cycles=int(getattr(args, "cycles", 1) or 1),
            auto_seed_gaps=not bool(getattr(args, "topic", None)),
        )
        print(json.dumps(result, indent=2, default=str)[:30000])
        return

    if sub == "status":
        print(json.dumps(cycle.status(), indent=2, default=str))
        return

    if sub == "seed":
        topic = getattr(args, "topic", None)
        if topic:
            out = cycle.seed_topic(
                topic,
                count=int(getattr(args, "count", 5) or 5),
                domain=str(getattr(args, "domain", "software") or "software"),
            )
        else:
            out = cycle.seed_from_gaps(limit=int(getattr(args, "max_items", 10) or 10))
        print(json.dumps(out, indent=2, default=str))
        return

    if sub == "once":
        out = cycle.run_once(
            max_items=int(getattr(args, "max_items", 5) or 5),
            auto_seed_gaps=True,
        )
        print(json.dumps(out, indent=2, default=str)[:30000])
        return

    raise SystemExit(f"Unknown learn subcommand: {sub}")


def register_learn_parser(subparsers) -> None:
    """Attach ``learn`` argparse group to the root ``om-ai`` parser."""
    learn = subparsers.add_parser(
        "learn",
        help="OM Autonomous Learning Command Layer (background distill → train queue)",
    )
    ls = learn.add_subparsers(dest="learn_sub", required=True)

    start = ls.add_parser(
        "start",
        help="Start one or more improvement cycles (gaps/topic → distill → training queue)",
    )
    start.add_argument("--topic", default="", help="Optional topic to seed curriculum")
    start.add_argument("--count", type=int, default=5, help="Questions when --topic is set")
    start.add_argument("--domain", default="software", help="Curriculum domain")
    start.add_argument("--max-items", type=int, default=5, help="Jobs per cycle")
    start.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    start.set_defaults(func=learn_cmd)

    status = ls.add_parser("status", help="Show learning scheduler + training queue status")
    status.set_defaults(func=learn_cmd)

    seed = ls.add_parser("seed", help="Enqueue jobs from gaps or a topic (do not run yet)")
    seed.add_argument("--topic", default="", help="Topic curriculum to enqueue")
    seed.add_argument("--count", type=int, default=5)
    seed.add_argument("--domain", default="software")
    seed.add_argument("--max-items", type=int, default=10, help="Gap limit when no --topic")
    seed.set_defaults(func=learn_cmd)

    once = ls.add_parser("once", help="Run a single improvement cycle tick")
    once.add_argument("--max-items", type=int, default=5)
    once.set_defaults(func=learn_cmd)
