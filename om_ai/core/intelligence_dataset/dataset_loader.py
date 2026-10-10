"""
OM Intelligence Dataset Loader.

Supported:

- JSON
- JSONL
- CSV
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator


class DatasetLoader:

    # =========================================================
    # JSON
    # =========================================================

    def load_json(
        self,
        path: str | Path,
    ) -> Iterator[dict[str, Any]]:

        file_path = Path(path)

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            dict,
        ):

            if isinstance(
                data.get("items"),
                list,
            ):

                for item in data["items"]:

                    if isinstance(
                        item,
                        dict,
                    ):

                        yield item

            else:

                yield data

        elif isinstance(
            data,
            list,
        ):

            for item in data:

                if isinstance(
                    item,
                    dict,
                ):

                    yield item

    # =========================================================
    # JSONL
    # =========================================================

    def load_jsonl(
        self,
        path: str | Path,
    ) -> Iterator[dict[str, Any]]:

        file_path = Path(path)

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:

                    continue

                data = json.loads(
                    line
                )

                if isinstance(
                    data,
                    dict,
                ):

                    yield data

    # =========================================================
    # CSV
    # =========================================================

    def load_csv(
        self,
        path: str | Path,
    ) -> Iterator[dict[str, Any]]:

        file_path = Path(path)

        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                yield dict(row)

    # =========================================================
    # AUTO
    # =========================================================

    def load(
        self,
        path: str | Path,
    ) -> Iterator[dict[str, Any]]:

        file_path = Path(path)

        suffix = (
            file_path.suffix.lower()
        )

        if suffix == ".json":

            yield from self.load_json(
                file_path
            )

            return

        if suffix == ".jsonl":

            yield from self.load_jsonl(
                file_path
            )

            return

        if suffix == ".csv":

            yield from self.load_csv(
                file_path
            )

            return

        raise ValueError(
            "Unsupported dataset format: "
            f"{suffix}. "
            "Supported formats: "
            ".json, .jsonl, .csv"
        )