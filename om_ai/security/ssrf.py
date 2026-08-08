"""SSRF protection guard for OM AI.

Validates URLs before outbound HTTP calls to block requests to private,
link-local, metadata, and loopback addresses.
"""
from __future__ import annotations

import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_BLOCKED_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("ff00::/8"),
    ipaddress.ip_network("0.0.0.0/8"),
]

_BLOCKED_HOSTS: frozenset[str] = frozenset(
    {
        "metadata.google.internal",
        "169.254.169.254",
    }
)


def _load_allowlist() -> frozenset[str]:
    raw = os.getenv("OM_AI_URL_ALLOWLIST", "").strip()
    if not raw:
        return frozenset()
    return frozenset(h.strip().lower() for h in raw.split(",") if h.strip())


class SSRFGuard:
    """Validates URLs to block Server-Side Request Forgery attacks.

    Usage::

        guard = SSRFGuard()
        guard.validate_url("https://api.example.com/v1/data")  # OK
        guard.validate_url("http://169.254.169.254/latest/meta-data/")  # raises ValueError
    """

    def __init__(self) -> None:
        self._allowlist: frozenset[str] = _load_allowlist()

    def reload_allowlist(self) -> None:
        """Hot-reload allowlist from environment."""
        self._allowlist = _load_allowlist()

    def _is_ip_blocked(self, addr: str) -> bool:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        return any(ip in net for net in _BLOCKED_NETWORKS)

    def validate_url(self, url: str) -> None:
        """Raise ValueError if *url* targets a private/blocked destination.

        Resolves the hostname to all A/AAAA records and checks every one.
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string.")

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError(
                f"Scheme '{scheme}' is not permitted. Only http/https are allowed."
            )

        host = parsed.hostname
        if not host:
            raise ValueError(f"URL has no resolvable host: {url!r}")

        host_lower = host.lower()

        if host_lower in _BLOCKED_HOSTS:
            raise ValueError(f"Host '{host}' is explicitly blocked (SSRF protection).")

        try:
            ipaddress.ip_address(host_lower)
            is_raw_ip = True
        except ValueError:
            is_raw_ip = False

        if is_raw_ip:
            if self._is_ip_blocked(host_lower):
                raise ValueError(
                    f"URL targets a private/reserved IP address: {host!r}"
                )
            return

        if host_lower in self._allowlist:
            logger.debug("SSRFGuard: '%s' is explicitly allowed.", host)
            return

        try:
            infos = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"Cannot resolve host '{host}': {exc}") from exc

        resolved_ips: set[str] = {info[4][0] for info in infos}
        logger.debug("SSRFGuard: '%s' resolved to %s", host, resolved_ips)

        for ip_str in resolved_ips:
            if self._is_ip_blocked(ip_str):
                raise ValueError(
                    f"Host '{host}' resolves to private/reserved IP '{ip_str}' "
                    f"(SSRF protection)."
                )

        port = parsed.port
        if port is not None and port not in range(1, 65536):
            raise ValueError(f"Invalid port: {port}")

    # Aliases for callers that use the check_url / safe_url API
    def check_url(self, url: str) -> None:
        """Alias for validate_url — raises SSRFError (ValueError subclass) if unsafe."""
        try:
            self.validate_url(url)
        except ValueError as exc:
            raise SSRFError(str(exc)) from exc

    def safe_url(self, url: str) -> str:
        """Return url unchanged after validation; raise SSRFError if unsafe."""
        self.check_url(url)
        return url


class SSRFError(ValueError):
    """Raised when a URL is deemed unsafe for outbound fetching (SSRF protection)."""
