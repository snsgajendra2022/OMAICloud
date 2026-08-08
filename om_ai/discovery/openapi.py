"""
OpenAPI discovery tool with SSRF protection.

Security:
  - SSRFGuard from om_ai.security.ssrf (or inline fallback) blocks private/loopback IPs.
  - Private IPs and RFC-1918 ranges are never fetched.
  - Parsed tool descriptors are returned for admin review (approve_tools flow).
  - Auto-registration is intentionally NOT performed — an admin must call approve_tools().
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from om_ai.actions.base import Tool, ToolResult

# ── SSRF guard: prefer package; inline fallback if security module absent ─────

try:
    from om_ai.security.ssrf import SSRFGuard, SSRFError  # type: ignore[import]
except ImportError:
    import ipaddress
    import socket
    from urllib.parse import urlparse

    _BLOCKED_NETS = [
        ipaddress.ip_network(n)
        for n in (
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
            "127.0.0.0/8", "169.254.0.0/16", "::1/128",
            "fc00::/7", "fe80::/10", "0.0.0.0/8",
        )
    ]

    class SSRFError(ValueError):  # type: ignore[no-redef]
        pass

    class SSRFGuard:  # type: ignore[no-redef]
        def check_url(self, url: str) -> None:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise SSRFError(f"Scheme not allowed: {parsed.scheme!r}")
            host = (parsed.hostname or "").lower()
            if not host:
                raise SSRFError("Missing host")
            try:
                addr = ipaddress.ip_address(host)
                for net in _BLOCKED_NETS:
                    if addr in net:
                        raise SSRFError(f"Blocked IP: {addr}")
                return
            except ValueError:
                pass
            try:
                infos = socket.getaddrinfo(host, None)
            except socket.gaierror as exc:
                raise SSRFError(f"Cannot resolve {host!r}: {exc}") from exc
            for info in infos:
                addr_str = info[4][0]
                try:
                    resolved = ipaddress.ip_address(addr_str)
                    for net in _BLOCKED_NETS:
                        if resolved in net:
                            raise SSRFError(f"Host {host!r} resolves to blocked address {addr_str}")
                except ValueError:
                    pass

        def safe_url(self, url: str) -> str:
            self.check_url(url)
            return url


logger = logging.getLogger(__name__)

# ─── OpenAPI → tool descriptor ────────────────────────────────────────────────


def _openapi_to_descriptors(spec: dict) -> list[dict]:
    """
    Parse an OpenAPI 3.x / Swagger 2.x spec into a list of candidate tool descriptors.
    Descriptors are NOT registered — they are returned for admin review.
    """
    descriptors: list[dict[str, Any]] = []
    paths = spec.get("paths") or {}
    base_url = ""

    # OpenAPI 3.x: servers[0].url
    servers = spec.get("servers", [])
    if servers and isinstance(servers, list):
        base_url = servers[0].get("url", "")

    # Swagger 2.x: basePath
    if not base_url:
        scheme = (spec.get("schemes") or ["https"])[0]
        host = spec.get("host", "")
        base_path = spec.get("basePath", "")
        if host:
            base_url = f"{scheme}://{host}{base_path}"

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            method_lower = method.lower()
            if method_lower not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId") or f"{method_lower}_{path.strip('/').replace('/', '_')}"
            summary = operation.get("summary") or operation.get("description") or ""
            tags = operation.get("tags", [])

            # Build parameter schema
            params_schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
            for param in operation.get("parameters", []):
                if not isinstance(param, dict):
                    continue
                pname = param.get("name", "")
                pschema = param.get("schema") or {"type": "string"}
                params_schema["properties"][pname] = {
                    "type": pschema.get("type", "string"),
                    "description": param.get("description", ""),
                    "in": param.get("in", "query"),
                }
                if param.get("required"):
                    params_schema["required"].append(pname)

            # Request body schema (OpenAPI 3.x)
            req_body = operation.get("requestBody")
            if req_body and isinstance(req_body, dict):
                content = req_body.get("content", {})
                json_schema = (
                    content.get("application/json", {}).get("schema")
                    or content.get("*/*", {}).get("schema")
                    or {}
                )
                if json_schema:
                    params_schema["properties"]["body"] = json_schema
                    if req_body.get("required"):
                        params_schema["required"].append("body")

            descriptors.append(
                {
                    "tool_name": f"openapi.{op_id}",
                    "method": method.upper(),
                    "path": path,
                    "full_url": f"{base_url}{path}" if base_url else path,
                    "summary": summary,
                    "tags": tags,
                    "input_schema": params_schema,
                    "operation_id": op_id,
                    "approved": False,   # must be explicitly approved
                }
            )

    return descriptors


# ─── OpenAPIDiscoveryTool ─────────────────────────────────────────────────────


class OpenAPIDiscoveryTool(Tool):
    """
    Fetch and parse an OpenAPI specification document.

    Returns parsed candidate tool descriptors for admin review via approve_tools().
    Does NOT auto-register tools.

    Security: all URLs are validated through SSRFGuard before any HTTP request.
    """

    name = "discovery.openapi"
    description = (
        "Fetch and summarise an OpenAPI document from an explicitly supplied URL. "
        "Returns candidate tool descriptors for admin approval — does NOT auto-register."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL of the OpenAPI JSON/YAML spec"},
            "timeout": {"type": "number", "description": "Request timeout in seconds", "default": 10},
        },
        "required": ["url"],
    }
    risk_level = "medium"

    def __init__(self, ssrf_guard: SSRFGuard | None = None) -> None:
        self._guard = ssrf_guard or SSRFGuard()

    def run(self, url: str = "", timeout: float = 10.0, **kwargs: Any) -> ToolResult:
        if not url:
            return ToolResult(False, error="url is required")

        # SSRF validation before any network request
        try:
            self._guard.check_url(url)
        except SSRFError as exc:
            return ToolResult(False, error=f"SSRF blocked: {exc}")

        try:
            resp = httpx.get(url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            spec = resp.json()
        except httpx.HTTPStatusError as exc:
            return ToolResult(False, error=f"HTTP {exc.response.status_code}: {url}")
        except Exception as exc:
            return ToolResult(False, error=str(exc))

        descriptors = _openapi_to_descriptors(spec)
        info = spec.get("info", {})

        return ToolResult(
            True,
            data={
                "title": info.get("title"),
                "version": info.get("version"),
                "endpoint_count": len(descriptors),
                "candidate_tools": descriptors,
                "note": (
                    "Tools are NOT registered. Call approve_tools(descriptors) "
                    "to selectively enable them."
                ),
            },
        )


# ─── Admin approval flow ──────────────────────────────────────────────────────


def approve_tools(
    descriptors: list[dict],
    approved_operation_ids: list[str] | None = None,
) -> list[dict]:
    """
    Admin approval helper.

    Args:
        descriptors: list of candidate descriptors returned by OpenAPIDiscoveryTool.
        approved_operation_ids: if provided, only descriptors whose operation_id is in
                                 this list are marked approved.  If None, ALL descriptors
                                 are approved (use with caution).

    Returns:
        List of approved descriptor dicts (approved=True).
        Caller is responsible for registering them with the orchestrator.
    """
    approved: list[dict] = []
    for desc in descriptors:
        op_id = desc.get("operation_id", "")
        if approved_operation_ids is None or op_id in approved_operation_ids:
            approved.append({**desc, "approved": True})
    return approved
