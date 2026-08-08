"""Checkpoint bundle management for OM AI model artefacts.

Bundle layout::

    <root>/models/OM-LM-<name>/
        config.json
        tokenizer/
            (copied/symlinked tokenizer vocab files)
        model/
            model.pt  (or model-shard-000.pt, …)
        optimizer/
            optimizer.pt          (optional)
        scheduler/
            scheduler.pt          (optional)
        training_state.json
        dataset_manifest.json
        evaluation.json
        provenance.json
        SHA256SUMS.txt

Public API
----------
save_bundle(root, model_state, model_config_dict, tokenizer_path, *, …)
load_bundle(root)
verify_integrity(root)
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclass for the bundle metadata
# ---------------------------------------------------------------------------


@dataclass
class CheckpointBundle:
    """In-memory representation of a checkpoint bundle."""

    root: Path
    model_name: str
    config: dict[str, Any]
    training_state: dict[str, Any]
    dataset_manifest: dict[str, Any]
    evaluation: dict[str, Any]
    provenance: dict[str, Any]

    # Optional loaded states (None until load_bundle() is called)
    model_state: Optional[dict[str, Any]] = field(default=None, repr=False)
    optimizer_state: Optional[dict[str, Any]] = field(default=None, repr=False)
    scheduler_state: Optional[dict[str, Any]] = field(default=None, repr=False)

    @property
    def bundle_dir(self) -> Path:
        return self.root / "models" / self.model_name

    @property
    def is_production_ready(self) -> bool:
        return (
            self.provenance.get("trained") is True
            and self.provenance.get("release_state") == "production"
        )


# ---------------------------------------------------------------------------
# SHA-256 utilities
# ---------------------------------------------------------------------------


def _sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while data := fh.read(chunk):
            h.update(data)
    return h.hexdigest()


def _write_sha256sums(bundle_dir: Path) -> Path:
    """Write SHA256SUMS.txt for all regular files in *bundle_dir*."""
    sums_path = bundle_dir / "SHA256SUMS.txt"
    lines: list[str] = []

    for path in sorted(bundle_dir.rglob("*")):
        if path.is_file() and path != sums_path:
            relative = path.relative_to(bundle_dir)
            digest = _sha256_file(path)
            lines.append(f"{digest}  {relative}")

    sums_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums_path


def _read_sha256sums(bundle_dir: Path) -> dict[str, str]:
    """Parse SHA256SUMS.txt -> {relative_path: digest}."""
    sums_path = bundle_dir / "SHA256SUMS.txt"
    if not sums_path.exists():
        raise FileNotFoundError(f"SHA256SUMS.txt not found in {bundle_dir}")

    result: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, rel_path = parts
        result[rel_path.strip()] = digest.strip()
    return result


# ---------------------------------------------------------------------------
# save_bundle
# ---------------------------------------------------------------------------


def save_bundle(
    root: str | os.PathLike,
    model_state: dict[str, Any],
    model_config_dict: dict[str, Any],
    tokenizer_path: str | os.PathLike,
    *,
    model_name: str = "OM-LM-custom",
    optimizer_state: Optional[dict[str, Any]] = None,
    scheduler_state: Optional[dict[str, Any]] = None,
    training_state: Optional[dict[str, Any]] = None,
    dataset_manifest: Optional[dict[str, Any]] = None,
    evaluation: Optional[dict[str, Any]] = None,
    provenance: Optional[dict[str, Any]] = None,
    trained: bool = False,
) -> Path:
    """Save a checkpoint bundle and return the bundle directory path.

    Parameters
    ----------
    root:
        Project root (``models/OM-LM-<name>/`` will be created under it).
    model_state:
        A ``state_dict``-like mapping (string keys → any serialisable value).
        Pass ``model.state_dict()`` from PyTorch. The bundle does **not** load
        actual weight tensors—it serialises whatever is provided with
        ``torch.save`` when available, or ``json`` for plain dicts.
    model_config_dict:
        Model architecture config (vocab_size, n_layers, …).
    tokenizer_path:
        Path to tokenizer directory or single vocab file; contents are copied
        into ``tokenizer/`` inside the bundle.
    trained:
        Must be ``True`` to allow ``release_state=production`` in provenance.
        If ``False`` and provenance contains ``release_state=production`` the
        call raises ``ValueError``.
    """
    root = Path(root)
    tokenizer_src = Path(tokenizer_path)

    # Validate trained / release_state guard
    prov = dict(provenance or {})
    prov["trained"] = bool(trained)
    prov.setdefault("bundle_created_at", datetime.now(timezone.utc).isoformat())
    prov.setdefault("model_name", model_name)

    if not trained and prov.get("release_state") == "production":
        raise ValueError(
            "Cannot set release_state=production when trained=False. "
            "The model has not been trained—refusing to mark it production."
        )

    bundle_dir = root / "models" / model_name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # --- config.json -------------------------------------------------------
    config_path = bundle_dir / "config.json"
    config_path.write_text(
        json.dumps(model_config_dict, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # --- tokenizer/ --------------------------------------------------------
    tok_dir = bundle_dir / "tokenizer"
    tok_dir.mkdir(exist_ok=True)
    if tokenizer_src.is_dir():
        for child in tokenizer_src.iterdir():
            dest = tok_dir / child.name
            if child.is_file():
                shutil.copy2(child, dest)
            elif child.is_dir():
                shutil.copytree(child, dest, dirs_exist_ok=True)
    elif tokenizer_src.is_file():
        shutil.copy2(tokenizer_src, tok_dir / tokenizer_src.name)
    else:
        logger.warning(
            "tokenizer_path '%s' does not exist – tokenizer/ will be empty.",
            tokenizer_src,
        )

    # --- model/ ------------------------------------------------------------
    model_dir = bundle_dir / "model"
    model_dir.mkdir(exist_ok=True)
    model_pt = model_dir / "model.pt"
    _save_state(model_state, model_pt)

    # --- optimizer/ --------------------------------------------------------
    if optimizer_state is not None:
        opt_dir = bundle_dir / "optimizer"
        opt_dir.mkdir(exist_ok=True)
        _save_state(optimizer_state, opt_dir / "optimizer.pt")

    # --- scheduler/ --------------------------------------------------------
    if scheduler_state is not None:
        sch_dir = bundle_dir / "scheduler"
        sch_dir.mkdir(exist_ok=True)
        _save_state(scheduler_state, sch_dir / "scheduler.pt")

    # --- training_state.json -----------------------------------------------
    ts: dict[str, Any] = dict(training_state or {})
    ts.setdefault("saved_at", datetime.now(timezone.utc).isoformat())
    (bundle_dir / "training_state.json").write_text(
        json.dumps(ts, indent=2, default=str), encoding="utf-8"
    )

    # --- dataset_manifest.json ---------------------------------------------
    dm: dict[str, Any] = dict(dataset_manifest or {})
    dm.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    (bundle_dir / "dataset_manifest.json").write_text(
        json.dumps(dm, indent=2, default=str), encoding="utf-8"
    )

    # --- evaluation.json ---------------------------------------------------
    ev: dict[str, Any] = dict(evaluation or {})
    ev.setdefault("recorded_at", datetime.now(timezone.utc).isoformat())
    (bundle_dir / "evaluation.json").write_text(
        json.dumps(ev, indent=2, default=str), encoding="utf-8"
    )

    # --- provenance.json ---------------------------------------------------
    (bundle_dir / "provenance.json").write_text(
        json.dumps(prov, indent=2, default=str), encoding="utf-8"
    )

    # --- SHA256SUMS.txt ----------------------------------------------------
    sums_path = _write_sha256sums(bundle_dir)

    logger.info(
        "Checkpoint bundle saved: %s  (trained=%s, files=%d)",
        bundle_dir,
        trained,
        sum(1 for _ in bundle_dir.rglob("*") if _.is_file()),
    )
    return bundle_dir


def _save_state(state: dict[str, Any], path: Path) -> None:
    """Serialise *state* to *path* using torch.save if available, else JSON."""
    try:
        import torch  # type: ignore[import]
        torch.save(state, str(path))
    except ImportError:
        # Fall back to JSON for non-tensor states (testing, config-only bundles)
        path.with_suffix(".json").write_text(
            json.dumps(state, indent=2, default=str), encoding="utf-8"
        )
        logger.debug("torch not available; saved state as JSON: %s", path)


def _load_state(path: Path) -> Optional[dict[str, Any]]:
    """Load a state dict from *path* or its JSON fallback."""
    if path.exists():
        try:
            import torch  # type: ignore[import]
            return torch.load(str(path), weights_only=True, map_location="cpu")
        except ImportError:
            pass
        except Exception as exc:
            logger.warning("torch.load failed for %s: %s – trying JSON.", path, exc)

    # Try JSON fallback
    json_path = path.with_suffix(".json")
    if json_path.exists():
        return json.loads(json_path.read_text(encoding="utf-8"))

    return None


# ---------------------------------------------------------------------------
# load_bundle
# ---------------------------------------------------------------------------


def load_bundle(root: str | os.PathLike, model_name: Optional[str] = None) -> CheckpointBundle:
    """Load a checkpoint bundle from *root*.

    If *model_name* is omitted, the first ``models/OM-LM-*`` directory is used.
    Returns a :class:`CheckpointBundle` with states loaded into memory.
    """
    root = Path(root)
    models_dir = root / "models"

    if model_name:
        bundle_dir = models_dir / model_name
    else:
        candidates = sorted(models_dir.iterdir()) if models_dir.exists() else []
        if not candidates:
            raise FileNotFoundError(f"No model bundles found under {models_dir}")
        bundle_dir = candidates[0]
        model_name = bundle_dir.name

    if not bundle_dir.is_dir():
        raise FileNotFoundError(f"Bundle directory not found: {bundle_dir}")

    def _load_json(name: str) -> dict[str, Any]:
        p = bundle_dir / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {}

    bundle = CheckpointBundle(
        root=root,
        model_name=model_name,
        config=_load_json("config.json"),
        training_state=_load_json("training_state.json"),
        dataset_manifest=_load_json("dataset_manifest.json"),
        evaluation=_load_json("evaluation.json"),
        provenance=_load_json("provenance.json"),
        model_state=_load_state(bundle_dir / "model" / "model.pt"),
        optimizer_state=_load_state(bundle_dir / "optimizer" / "optimizer.pt"),
        scheduler_state=_load_state(bundle_dir / "scheduler" / "scheduler.pt"),
    )

    logger.info("Loaded bundle '%s' from %s (trained=%s)",
                model_name, root, bundle.provenance.get("trained"))
    return bundle


# ---------------------------------------------------------------------------
# verify_integrity
# ---------------------------------------------------------------------------


def verify_integrity(root: str | os.PathLike, model_name: Optional[str] = None) -> bool:
    """Verify SHA256 checksums for all files in the bundle.

    Returns True if all hashes match. Raises ValueError describing the first
    mismatch. Raises FileNotFoundError if SHA256SUMS.txt is missing.
    """
    root = Path(root)
    models_dir = root / "models"

    if model_name:
        bundle_dir = models_dir / model_name
    else:
        candidates = sorted(models_dir.iterdir()) if models_dir.exists() else []
        if not candidates:
            raise FileNotFoundError(f"No model bundles found under {models_dir}")
        bundle_dir = candidates[0]

    expected = _read_sha256sums(bundle_dir)
    mismatches: list[str] = []
    missing: list[str] = []

    for rel_str, expected_digest in expected.items():
        file_path = bundle_dir / rel_str
        if not file_path.exists():
            missing.append(rel_str)
            continue
        actual_digest = _sha256_file(file_path)
        if actual_digest != expected_digest:
            mismatches.append(
                f"{rel_str}: expected {expected_digest[:16]}… got {actual_digest[:16]}…"
            )

    if missing:
        raise ValueError(f"Missing files in bundle: {missing}")
    if mismatches:
        raise ValueError(f"SHA256 mismatch(es) detected:\n" + "\n".join(mismatches))

    logger.info("verify_integrity: all %d files OK in %s", len(expected), bundle_dir)
    return True
