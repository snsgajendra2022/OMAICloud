from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import om_ai.security.auth as auth_module


class _EmptyTokenStore:
    def list(self):
        return []


def _patch_empty_credentials(monkeypatch):
    from om_ai.security import tokens

    monkeypatch.setattr(auth_module, "_load_api_keys", lambda: {})
    monkeypatch.setattr(tokens, "get_token_store", lambda: _EmptyTokenStore())


def test_auth_fails_closed_without_credentials(monkeypatch):
    _patch_empty_credentials(monkeypatch)
    monkeypatch.delenv("OM_AI_ALLOW_OPEN_DEV_MODE", raising=False)
    monkeypatch.delenv("OM_AI_REQUIRE_AUTH", raising=False)

    with pytest.warns(UserWarning, match="fail-closed"):
        auth = auth_module.APIKeyAuth()

    assert auth.is_dev_mode() is False


def test_open_dev_mode_requires_explicit_opt_in(monkeypatch):
    _patch_empty_credentials(monkeypatch)
    monkeypatch.setenv("OM_AI_ALLOW_OPEN_DEV_MODE", "1")
    monkeypatch.delenv("OM_AI_REQUIRE_AUTH", raising=False)

    with pytest.warns(UserWarning, match="loopback/local development"):
        auth = auth_module.APIKeyAuth()

    assert auth.is_dev_mode() is True


def test_strict_auth_overrides_open_dev_opt_in(monkeypatch):
    _patch_empty_credentials(monkeypatch)
    monkeypatch.setenv("OM_AI_ALLOW_OPEN_DEV_MODE", "1")
    monkeypatch.setenv("OM_AI_REQUIRE_AUTH", "1")

    with pytest.warns(UserWarning, match="fail-closed"):
        auth = auth_module.APIKeyAuth()

    assert auth.is_dev_mode() is False


def test_open_dev_mode_rejects_non_loopback_clients(monkeypatch):
    _patch_empty_credentials(monkeypatch)
    monkeypatch.setenv("OM_AI_ALLOW_OPEN_DEV_MODE", "1")
    monkeypatch.delenv("OM_AI_REQUIRE_AUTH", raising=False)

    with pytest.warns(UserWarning):
        auth = auth_module.APIKeyAuth()

    monkeypatch.setattr(auth_module, "_get_auth", lambda: auth)
    request = SimpleNamespace(
        headers={},
        client=SimpleNamespace(host="192.0.2.10"),
    )

    with pytest.raises(HTTPException) as exc:
        auth_module._resolve_context_from_request(request)

    assert exc.value.status_code == 403
