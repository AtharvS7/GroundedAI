"""FastAPI dependency injection module."""

from __future__ import annotations

from app.api.middleware.auth import get_current_user


# Re-export for cleaner imports
__all__ = ["get_current_user"]
