"""Auth route package — re-exports the production auth router.

Registration / login live in `om_ai.api.auth_routes`.
Onboarding is triggered there after register (and lazily on login if needed).
"""
from __future__ import annotations

from om_ai.api.auth_routes import router

__all__ = ["router"]
