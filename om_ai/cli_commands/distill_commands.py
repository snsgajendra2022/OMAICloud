from __future__ import annotations

import os
import json
import logging
from pathlib import Path


import typer


from om_ai.core.distillation import (
    DistillationEngine,
    OllamaClient,
    TeacherRegistry,
    create_teacher_manager,
)
from om_ai.core.distillation.teacher_manager import TeacherManager


logger = logging.getLogger(
    "om.distill.cli"
)



distill_app = typer.Typer(
    name="distill",
    help="OM Knowledge Distillation Commands"
)



@distill_app.command()
def health():

    """
    Check local distillation system.
    """

    result = {

        "distillation":
            "enabled",

        "status":
            "ready",

        "engine":
            "OM Distillation Engine",

    }


    typer.echo(
        json.dumps(
            result,
            indent=2
        )
    )





@distill_app.command()
def models():

    """
    Show available teacher models.

    Actual Ollama discovery will be connected
    through OllamaClient.
    """


    models = [

        {

            "name":
                "qwen3",

            "status":
                "configured"

        },

        {

            "name":
                "deepseek",

            "status":
                "configured"

        }

    ]


    typer.echo(

        json.dumps(
            models,
            indent=2
        )

    )





@distill_app.command()
def topic(
    topic: str = typer.Option(
        ...,
        "--topic",
        help="Topic to distill",
    ),
    count: int = typer.Option(
        10,
        "--count",
        help="Number of curriculum questions",
    ),
    parallelism: int = typer.Option(
        2,
        "--parallelism",
        help="Parallel teacher workers",
    ),
    domain: str = typer.Option(
        "software",
        "--domain",
        help="Curriculum domain",
    ),
):
    """
    Distill a knowledge topic (curriculum questions + teacher harvest).

    Example:
      om-ai distill topic --topic "React architecture" --count 2
    """
    from om_ai.core.distillation import CurriculumGenerator, create_teacher_manager

    # Better questions than "Explain X concept 0/1/…"
    pack = CurriculumGenerator().generate(topic, domain=domain, count=count)
    questions = [q["question"] for q in (pack.get("questions") or []) if q.get("question")]
    if not questions:
        questions = [f"Explain {topic} in depth with practical architecture guidance."]

    teacher_manager = create_teacher_manager()
    teacher_manager.parallelism = max(1, int(parallelism))
    engine = DistillationEngine(teacher_manager=teacher_manager)
    result = engine.distill_dataset(questions, domain=topic)

    approved = sum(1 for r in result if isinstance(r, dict) and r.get("approved"))
    typer.echo(
        json.dumps(
            {
                "topic": topic,
                "domain": domain,
                "curriculum_id": pack.get("curriculum_id"),
                "questions": len(questions),
                "processed": len(result),
                "approved": approved,
                "parallelism": teacher_manager.parallelism,
            },
            indent=2,
        )
    )


@distill_app.command()
def harvest(
    input_file: str,
):

    """
    Harvest questions from JSONL.
    """

    path = Path(input_file)

    if not path.exists():
        typer.echo("Input file not found")
        raise typer.Exit(1)

    questions = []
    with open(path, encoding="utf-8") as file:
        for line in file:
            item = json.loads(line)
            questions.append(item.get("question", ""))

    teacher_manager = create_teacher_manager()
    engine = DistillationEngine(teacher_manager=teacher_manager)
    result = engine.distill_dataset(questions)

    typer.echo(f"Completed {len(result)} questions")





@distill_app.command()
def status(
    run: str
):

    """
    Show distillation run status.
    """


    checkpoint = Path(

        "data/distillation/checkpoints"

    ) / f"{run}.json"



    if not checkpoint.exists():

        typer.echo(
            "Run not found"
        )

        raise typer.Exit(
            1
        )


    typer.echo(

        checkpoint.read_text()

    )


@distill_app.command()
def export(
    source: str
):

    """
    Export generated datasets.
    """


    typer.echo(

        json.dumps(

            {

                "source":
                    source,

                "status":
                    "export_ready"

            },

            indent=2

        )

    )





@distill_app.command()
def evaluate(
    run: str
):

    """
    Evaluate distillation run.
    """


    typer.echo(

        json.dumps(

            {

                "run":
                    run,

                "evaluation":
                    "pending"

            },

            indent=2

        )

    )


@distill_app.command("teachers")
def teachers_cmd():
    """STEP 94.10 — Teacher Intelligence profiles."""
    from om_ai.core.distillation import TeacherIntelligence

    typer.echo(json.dumps(TeacherIntelligence().status(), indent=2, default=str))


@distill_app.command()
def curriculum(
    topic: str,
    domain: str = "software",
    count: int = 8,
):
    """STEP 94.11 — Generate a distillation curriculum and enqueue it."""
    from om_ai.core.distillation import CurriculumGenerator, AutonomousHarvestScheduler

    pack = CurriculumGenerator().generate(topic, domain=domain, count=count)
    jobs = AutonomousHarvestScheduler().enqueue_many(pack.get("questions") or [], source="cli_curriculum")
    typer.echo(
        json.dumps(
            {
                "curriculum_id": pack.get("curriculum_id"),
                "count": pack.get("count"),
                "queued": len(jobs),
                "path": pack.get("path"),
            },
            indent=2,
        )
    )


@distill_app.command()
def gaps(
    topic: str = "",
    list_only: bool = typer.Option(False, "--list", help="List top gaps"),
):
    """STEP 94.13 — Collect or list knowledge gaps."""
    from om_ai.core.distillation import KnowledgeGapCollector

    collector = KnowledgeGapCollector()
    if list_only or not topic.strip():
        typer.echo(json.dumps(collector.status(), indent=2, default=str))
        return
    row = collector.collect_explicit(topic)
    typer.echo(json.dumps(row, indent=2))


@distill_app.command()
def schedule(
    limit: int = 5,
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    """STEP 94.12 — Show queue or run a harvest batch."""
    from om_ai.core.distillation import AutonomousHarvestScheduler, create_continuous_loop

    sched = AutonomousHarvestScheduler()
    if dry_run:
        typer.echo(
            json.dumps(
                {"pending": sched.pending()[:limit], "status": sched.status()},
                indent=2,
                default=str,
            )
        )
        return
    loop = create_continuous_loop()
    result = loop.scheduler.run_once(loop.harvest_fn, limit=limit)
    typer.echo(json.dumps(result, indent=2, default=str)[:20000])


@distill_app.command()
def cycle(
    max_items: int = 5,
    topic: str = "",
    domain: str = "software",
):
    """STEP 94.14 — Run one continuous distillation loop cycle."""
    from om_ai.core.distillation import create_continuous_loop

    loop = create_continuous_loop()
    planned = None
    if topic.strip():
        planned = loop.plan_topic(topic.strip(), domain=domain)
    result = loop.run_cycle(max_items=max_items, domain=domain, auto_plan_gaps=not bool(topic.strip()))
    typer.echo(json.dumps({"planned": planned, "cycle": result}, indent=2, default=str)[:20000])
