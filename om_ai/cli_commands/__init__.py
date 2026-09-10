"""
OM AI CLI Commands Package

Contains command groups:

- Distillation commands (Typer group under distill routing)
- Learning commands (argparse handlers for ``om-ai learn``)
"""

from .distill_commands import distill_app
from .learn_commands import learn_cmd, register_learn_parser

__all__ = [
    "distill_app",
    "learn_cmd",
    "register_learn_parser",
]
