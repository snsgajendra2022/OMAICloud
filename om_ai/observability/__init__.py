"""OM AI observability package.

Exports
-------
TrainingMetricsLogger  – thread-safe JSONL metrics appender for training runs
MetricsCollector       – in-process counters for OMMonitor runtime health
MetricsRecord          – dataclass for one row of training telemetry
format_prometheus      – convert a metrics dict to Prometheus text-exposition format
write_prometheus_file  – atomically write a Prometheus ``/metrics`` scrape file
"""

from om_ai.observability.metrics import (
    MetricsCollector,
    MetricsRecord,
    TrainingMetricsLogger,
    format_prometheus,
    write_prometheus_file,
)
from .monitor import OMMonitor

from .events import EventTracker

from .health import HealthMonitor

__all__ = [
    "TrainingMetricsLogger",
    "MetricsRecord",
    "format_prometheus",
    "write_prometheus_file",
    "OMMonitor",
    "MetricsCollector",
    "EventTracker",
    "HealthMonitor"
]
