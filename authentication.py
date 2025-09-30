"""Optional HTTP Basic Auth for the Dash app."""

from __future__ import annotations

import os
from typing import Mapping, MutableMapping

import dash
import dash_auth


# Default credentials are meant for local development only
DEFAULT_CREDENTIALS: Mapping[str, str] = {"admin": "123"}


def _normalize_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def auth_enabled(default: bool = False) -> bool:
    """Detect whether Basic Auth should be enabled via env var."""
    return _normalize_bool(os.environ.get("ENABLE_DASH_AUTH"), default=default)


def resolve_credentials(
    username: str | None = None, password: str | None = None
) -> MutableMapping[str, str]:
    """Resolve credentials from args or environment with a dev fallback."""
    user = username or os.environ.get("DASH_AUTH_USERNAME")
    pwd = password or os.environ.get("DASH_AUTH_PASSWORD")
    if user and pwd:
        return {user: pwd}
    return dict(DEFAULT_CREDENTIALS)


def maybe_enable_basic_auth(
    app: dash.Dash,
    enabled: bool | None = None,
    credentials: Mapping[str, str] | None = None,
):
    """Attach BasicAuth to the app when enabled.

    Returns the dash-auth instance when auth is active, else ``None``.
    """

    active = auth_enabled() if enabled is None else enabled
    if not active:
        return None

    creds: Mapping[str, str] = credentials or resolve_credentials()
    if not creds:
        raise ValueError("Basic auth enabled but no credentials were provided")

    return dash_auth.BasicAuth(app, creds)
