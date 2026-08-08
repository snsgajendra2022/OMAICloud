"""OM AI Model Registry with lifecycle state management."""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from om_ai.model import OMTransformer

logger = logging.getLogger(__name__)

# Valid lifecycle states and allowed forward transitions.
# A model may not skip states (except deprecation from any state).
_VALID_STATES = frozenset(
    {"training", "candidate", "evaluated", "approved", "production", "deprecated"}
)

_STATE_TRANSITIONS: dict[str, frozenset[str]] = {
    "training":   frozenset({"candidate", "deprecated"}),
    "candidate":  frozenset({"evaluated", "deprecated"}),
    "evaluated":  frozenset({"approved", "deprecated"}),
    "approved":   frozenset({"production", "deprecated"}),
    "production": frozenset({"deprecated"}),
    "deprecated": frozenset(),
}


class RegistryError(Exception):
    """Raised on invalid registry operations."""


class ModelRegistry:
    """Filesystem-backed model registry with lifecycle management.

    Directory layout::

        <root>/
          <version>/
            weights.pt
            tokenizer.json
            metadata.json      ← version, state, checksum, benchmarks, …
    """

    def __init__(self, root: str | Path = "artifacts/registry") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Registration                                                         #
    # ------------------------------------------------------------------ #

    def register(
        self,
        version: str,
        model: OMTransformer,
        tokenizer_path: str,
        training_data_version: str,
        evaluation: dict[str, Any] | None = None,
        benchmarks: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        initial_state: str = "candidate",
        trained: bool = False,
    ) -> dict[str, Any]:
        """Save model weights + tokenizer and write structured metadata.

        Args:
            version: Unique string identifier (e.g. ``"v0.3.0-tiny"``).
            model: Trained ``OMTransformer`` instance.
            tokenizer_path: Path to the tokenizer JSON to copy.
            training_data_version: Version tag of the training corpus.
            evaluation: Optional dict of evaluation metric scores.
            benchmarks: Optional dict of benchmark results.
            provenance: Optional dict describing data sources, training config, etc.
            initial_state: Starting lifecycle state (default ``"candidate"``).
            trained: Whether the model has been through a training run.

        Returns:
            The metadata dict that was written to disk.
        """
        if initial_state not in _VALID_STATES:
            raise RegistryError(f"Invalid initial_state {initial_state!r}. Choose from {sorted(_VALID_STATES)}.")
        dest = self.root / version
        dest.mkdir(parents=True, exist_ok=False)

        weights = dest / "weights.pt"
        torch.save(model.state_dict(), weights)
        shutil.copy2(tokenizer_path, dest / "tokenizer.json")

        digest = hashlib.sha256(weights.read_bytes()).hexdigest()
        param_count = model.exact_parameter_count()

        metadata: dict[str, Any] = {
            "version": version,
            "state": initial_state,
            "trained": trained,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "model_config": asdict(model.cfg),
            "parameter_count": param_count,
            "training_data_version": training_data_version,
            "evaluation": evaluation or {},
            "benchmarks": benchmarks or {},
            "provenance": provenance or {},
            "sha256": digest,
        }
        (dest / "metadata.json").write_text(json.dumps(metadata, indent=2))
        logger.info("Registered model %s [%s] (%d params)", version, initial_state, param_count)
        return metadata

    # ------------------------------------------------------------------ #
    #  Lifecycle transitions                                                #
    # ------------------------------------------------------------------ #

    def promote(self, model_id: str, new_state: str) -> dict[str, Any]:
        """Transition *model_id* to *new_state*.

        Rules enforced:
        - Cannot jump over intermediate states.
        - Cannot promote to ``production`` without ``evaluation`` scores and ``trained=True``.
        - ``deprecated`` is always allowed from any non-deprecated state.

        Returns:
            Updated metadata dict.
        """
        if new_state not in _VALID_STATES:
            raise RegistryError(f"Unknown state {new_state!r}.")

        meta = self._load_meta(model_id)
        current = meta.get("state", "training")

        if new_state == current:
            return meta  # idempotent

        allowed = _STATE_TRANSITIONS.get(current, frozenset())
        if new_state not in allowed:
            raise RegistryError(
                f"Cannot transition '{model_id}' from '{current}' to '{new_state}'. "
                f"Allowed transitions: {sorted(allowed) or 'none'}."
            )

        if new_state == "production":
            if not meta.get("trained"):
                raise RegistryError(
                    f"Cannot promote '{model_id}' to production: metadata.trained is False. "
                    "Only models that have completed a training run may be promoted."
                )
            if not meta.get("evaluation"):
                raise RegistryError(
                    f"Cannot promote '{model_id}' to production: evaluation scores are missing. "
                    "Run evaluation and update the registry entry first."
                )

        meta["state"] = new_state
        meta["promoted_at"] = datetime.now(timezone.utc).isoformat()
        self._save_meta(model_id, meta)
        logger.info("Promoted %s: %s → %s", model_id, current, new_state)
        return meta

    def deprecate(self, model_id: str, reason: str = "") -> dict[str, Any]:
        """Shortcut to mark any model as deprecated."""
        meta = self._load_meta(model_id)
        if meta.get("state") == "deprecated":
            return meta
        meta["state"] = "deprecated"
        meta["deprecated_at"] = datetime.now(timezone.utc).isoformat()
        if reason:
            meta["deprecation_reason"] = reason
        self._save_meta(model_id, meta)
        logger.info("Deprecated %s: %s", model_id, reason)
        return meta

    def update_evaluation(self, model_id: str, evaluation: dict[str, Any]) -> dict[str, Any]:
        """Merge new evaluation scores into the model's metadata."""
        meta = self._load_meta(model_id)
        meta["evaluation"] = {**meta.get("evaluation", {}), **evaluation}
        meta["evaluated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_meta(model_id, meta)
        return meta

    # ------------------------------------------------------------------ #
    #  Queries                                                              #
    # ------------------------------------------------------------------ #

    def list_versions(self, state_filter: str | None = None) -> list[dict[str, Any]]:
        """Return metadata for all registered versions, ordered by creation time.

        Args:
            state_filter: If provided, only return models in this state.
        """
        out = []
        for p in sorted(self.root.iterdir()):
            meta_path = p / "metadata.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text())
            except Exception:
                continue
            if state_filter and meta.get("state") != state_filter:
                continue
            out.append(meta)
        return out

    def get(self, model_id: str) -> dict[str, Any]:
        """Return the metadata for a single model, raising KeyError if absent."""
        return self._load_meta(model_id)

    def list(self, state_filter: str | None = None) -> list[dict[str, Any]]:
        """Alias for list_versions (backward compatibility)."""
        return self.list_versions(state_filter=state_filter)

    # ------------------------------------------------------------------ #
    #  Internal                                                             #
    # ------------------------------------------------------------------ #

    def _load_meta(self, model_id: str) -> dict[str, Any]:
        path = self.root / model_id / "metadata.json"
        if not path.exists():
            raise KeyError(f"Model '{model_id}' not found in registry.")
        return json.loads(path.read_text())

    def _save_meta(self, model_id: str, meta: dict[str, Any]) -> None:
        path = self.root / model_id / "metadata.json"
        path.write_text(json.dumps(meta, indent=2))
