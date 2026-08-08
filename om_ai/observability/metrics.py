"""Training metrics logger and Prometheus text-exposition helpers for OM AI.

TrainingMetricsLogger – append structured JSONL metrics during/after training.
format_prometheus      – convert a metrics dict to Prometheus text-exposition format.

Example::

    logger = TrainingMetricsLogger("artifacts/metrics.jsonl")
    logger.log(step=100, loss=2.34, lr=3e-4, tokens_sec=12_500, grad_norm=0.9)

    # Optional Prometheus endpoint dump
    snapshot = logger.latest_snapshot()
    print(format_prometheus(snapshot))
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

log = logging.getLogger(__name__)

_DEFAULT_METRICS_PATH = os.getenv(
    "OM_AI_METRICS_FILE", "artifacts/training_metrics.jsonl"
)


# ---------------------------------------------------------------------------
# Metrics record
# ---------------------------------------------------------------------------


@dataclass
class MetricsRecord:
    """One row of training telemetry."""

    step: int
    loss: float
    lr: float
    tokens_sec: float
    grad_norm: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    epoch: Optional[int] = None
    val_loss: Optional[float] = None
    perplexity: Optional[float] = None
    # Arbitrary extra fields (DPO reward margins, RL scores, …)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        extra = d.pop("extra", {}) or {}
        d.update(extra)
        return d


# ---------------------------------------------------------------------------
# TrainingMetricsLogger
# ---------------------------------------------------------------------------


class TrainingMetricsLogger:
    """Append JSONL training metrics to a file, thread-safely.

    Each call to :meth:`log` writes one JSON line and updates an in-memory
    snapshot of the *latest* values for all tracked keys.

    Parameters
    ----------
    path:
        Destination JSONL file. Created (with parent dirs) if absent.
    flush_every:
        Flush to disk after every N records (1 = always flush, 0 = never).
    """

    def __init__(
        self,
        path: str | os.PathLike = _DEFAULT_METRICS_PATH,
        *,
        flush_every: int = 1,
    ) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._flush_every = max(0, flush_every)
        self._lock = threading.Lock()
        self._fh = open(self._path, "a", encoding="utf-8", buffering=1)  # line-buffered
        self._count = 0
        self._latest: dict[str, Any] = {}
        self._history: list[MetricsRecord] = []

    # ------------------------------------------------------------------
    # Core logging
    # ------------------------------------------------------------------

    def log(
        self,
        step: int,
        loss: float,
        lr: float,
        tokens_sec: float,
        grad_norm: float,
        *,
        epoch: Optional[int] = None,
        val_loss: Optional[float] = None,
        perplexity: Optional[float] = None,
        **extra: Any,
    ) -> None:
        """Write one metrics record to the JSONL file."""
        if perplexity is None and loss is not None:
            import math
            try:
                perplexity = math.exp(loss)
            except OverflowError:
                perplexity = float("inf")

        record = MetricsRecord(
            step=step,
            loss=float(loss),
            lr=float(lr),
            tokens_sec=float(tokens_sec),
            grad_norm=float(grad_norm),
            epoch=epoch,
            val_loss=float(val_loss) if val_loss is not None else None,
            perplexity=perplexity,
            extra=extra,
        )

        row = record.to_dict()
        line = json.dumps(row, ensure_ascii=False, default=str)

        with self._lock:
            self._fh.write(line + "\n")
            self._count += 1
            if self._flush_every and self._count % self._flush_every == 0:
                self._fh.flush()
            self._latest.update(row)
            self._history.append(record)

    def flush(self) -> None:
        with self._lock:
            self._fh.flush()

    def close(self) -> None:
        with self._lock:
            self._fh.flush()
            self._fh.close()

    def __enter__(self) -> "TrainingMetricsLogger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def latest_snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the latest tracked metric values."""
        with self._lock:
            return dict(self._latest)

    def history(self, last_n: Optional[int] = None) -> list[MetricsRecord]:
        """Return a copy of the in-memory history (optionally capped at *last_n*)."""
        with self._lock:
            records = list(self._history)
        if last_n is not None:
            records = records[-last_n:]
        return records

    def load_from_file(self) -> list[dict[str, Any]]:
        """Read and parse all JSONL lines from the metrics file on disk."""
        records: list[dict[str, Any]] = []
        if not self._path.exists():
            return records
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        log.warning("Skipping malformed metrics line: %s", exc)
        return records

    @property
    def record_count(self) -> int:
        with self._lock:
            return self._count

    @property
    def path(self) -> Path:
        return self._path


# ---------------------------------------------------------------------------
# Prometheus text exposition
# ---------------------------------------------------------------------------

_METRIC_HELP: dict[str, str] = {
    "step":        "Current training step",
    "loss":        "Training cross-entropy loss",
    "lr":          "Current learning rate",
    "tokens_sec":  "Throughput in tokens per second",
    "grad_norm":   "Gradient L2 norm",
    "epoch":       "Current training epoch",
    "val_loss":    "Validation cross-entropy loss",
    "perplexity":  "Model perplexity (exp(loss))",
}


def format_prometheus(
    metrics: dict[str, Any],
    *,
    namespace: str = "om_ai_training",
    labels: Optional[dict[str, str]] = None,
) -> str:
    """Convert a metrics snapshot dict to Prometheus text-exposition format.

    Parameters
    ----------
    metrics:
        Dict of metric_name -> numeric value (as returned by
        ``TrainingMetricsLogger.latest_snapshot()``).
    namespace:
        Prefix for all metric names (``om_ai_training`` by default).
    labels:
        Optional extra labels to attach to every metric, e.g.
        ``{"model": "OM-LM-7b", "run_id": "abc123"}``.

    Returns
    -------
    str
        Prometheus text format ready to be served at ``/metrics``.
    """
    label_str = ""
    if labels:
        label_str = "{" + ",".join(
            f'{k}="{_prom_escape(v)}"' for k, v in sorted(labels.items())
        ) + "}"

    lines: list[str] = []
    for key, value in metrics.items():
        if not isinstance(value, (int, float)):
            continue
        if key in ("timestamp",):
            continue

        metric_name = f"{namespace}_{key}"
        help_text = _METRIC_HELP.get(key, f"OM AI metric: {key}")

        lines.append(f"# HELP {metric_name} {help_text}")
        lines.append(f"# TYPE {metric_name} gauge")

        prom_value = _format_prom_value(value)
        lines.append(f"{metric_name}{label_str} {prom_value}")

    return "\n".join(lines) + "\n" if lines else ""


def write_prometheus_file(
    path: str | os.PathLike,
    metrics: dict[str, Any],
    *,
    namespace: str = "om_ai_training",
    labels: Optional[dict[str, str]] = None,
) -> None:
    """Atomically write a Prometheus text file to *path*.

    The write is atomic (write-to-tmp, rename) so a scraper never sees a
    partial file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = format_prometheus(metrics, namespace=namespace, labels=labels)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
    log.debug("Wrote Prometheus metrics to %s (%d bytes)", path, len(content))


def _prom_escape(s: str) -> str:
    """Escape a Prometheus label value."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _format_prom_value(v: Union[int, float]) -> str:
    if isinstance(v, float):
        if v != v:  # NaN
            return "NaN"
        if v == float("inf"):
            return "+Inf"
        if v == float("-inf"):
            return "-Inf"
    return repr(float(v))
