"""
OM Intelligence Dataset Validator.
"""

from __future__ import annotations

from typing import Any

from .dataset_item import DatasetItem


class DatasetValidationError(
    ValueError
):
    """Invalid dataset item."""


class DatasetValidator:


    MAX_INPUT_LENGTH = 50_000

    MAX_RESPONSE_LENGTH = 100_000


    def validate(
        self,
        item: DatasetItem,
    ) -> DatasetItem:

        errors: list[str] = []


        if not item.input_text.strip():

            errors.append(
                "input_text cannot be empty"
            )


        if not item.ideal_response.strip():

            errors.append(
                "ideal_response cannot be empty"
            )


        if len(
            item.input_text
        ) > self.MAX_INPUT_LENGTH:

            errors.append(
                "input_text exceeds maximum length"
            )


        if len(
            item.ideal_response
        ) > self.MAX_RESPONSE_LENGTH:

            errors.append(
                "ideal_response exceeds maximum length"
            )


        if not (
            0.0
            <= item.quality_score
            <= 1.0
        ):

            errors.append(
                "quality_score must be between 0 and 1"
            )


        if errors:

            raise DatasetValidationError(
                "; ".join(errors)
            )


        return item


    def validate_dict(
        self,
        data: dict[str, Any],
    ) -> DatasetItem:

        item = DatasetItem.from_dict(
            data
        )

        return self.validate(
            item
        )