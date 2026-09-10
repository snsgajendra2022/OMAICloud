from __future__ import annotations

import os
import json
import logging
from pathlib import Path


import typer


from om_ai.core.distillation import (
    DistillationEngine,
)

from om_ai.core.distillation import (
    DistillationEngine,
    OllamaClient,
    TeacherRegistry,
    TeacherManager,
)


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
    topic: str,
    count: int = 10,
):

    """
    Distill a knowledge topic.
    """


    questions = [

        f"Explain {topic} concept {i}"

        for i in range(count)

    ]


    client = OllamaClient(
        base_url= os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    )


    registry = TeacherRegistry(

        client,

        [
            "qwen3:14b",
            "deepseek-r1:14b",
            "mistral:latest"
        ]

    )


    teacher_manager = TeacherManager(

        client,

        registry,

        parallelism=2

    )

    engine = DistillationEngine(

        teacher_manager=teacher_manager

    )
    result = engine.distill_dataset(

        questions,

        domain=topic

    )


    typer.echo(

        json.dumps(
            {

                "topic":
                    topic,

                "processed":
                    len(result)

            },

            indent=2

        )

    )





@distill_app.command()
def harvest(
    input_file: str,
):

    """
    Harvest questions from JSONL.
    """


    path = Path(
        input_file
    )


    if not path.exists():

        typer.echo(
            "Input file not found"
        )

        raise typer.Exit(
            1
        )



    questions=[]



    with open(
        path,
        encoding="utf-8"
    ) as file:


        for line in file:


            item=json.loads(
                line
            )


            questions.append(

                item.get(
                    "question",
                    ""
                )

            )



    client = OllamaClient(
        base_url= os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    )


    registry = TeacherRegistry(

        client,

        [
            "qwen3:14b",
            "deepseek-r1:14b",
            "mistral:latest"
        ]

    )


    teacher_manager = TeacherManager(

        client,

        registry,

        parallelism=2

    )

    engine = DistillationEngine(

        teacher_manager=teacher_manager

    )


    result = engine.distill_dataset(
        questions
    )


    typer.echo(

        f"Completed {len(result)} questions"

    )





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