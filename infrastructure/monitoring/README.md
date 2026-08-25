# OM monitoring
Scrape targets:
- om-ai serve /health
- artifacts from `om-ai platform build` → infrastructure/monitoring/platform_metrics.json

Prometheus text can be emitted via `om_ai.observability.metrics.format_prometheus`.
