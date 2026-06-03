from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, ValidationError, model_validator

from growi_mcp_server.growi.errors import ConfigurationError


class Settings(BaseModel):
    """Validated application configuration loaded from environment variables."""

    model_config = ConfigDict(extra="forbid")

    growi_base_url: AnyHttpUrl
    growi_access_token: str
    growi_content_root: Path | None = None
    growi_timeout_ms: int = 30_000
    growi_verify_tls: bool = True
    growi_enable_write_tools: bool = False
    growi_user_agent: str = "growi-mcp-server/0.1"
    mcp_transport: Literal["stdio", "streamable-http"] = "stdio"
    mcp_http_host: str = "127.0.0.1"
    mcp_http_port: int = 8787
    mcp_http_path: str = "/mcp"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
        if not self.growi_access_token.strip():
            raise ValueError("GROWI_ACCESS_TOKEN must not be empty.")
        if not self.mcp_http_path.startswith("/"):
            raise ValueError("MCP_HTTP_PATH must start with '/'.")
        if self.growi_content_root is not None and not self.growi_content_root.exists():
            raise ValueError(f"GROWI_CONTENT_ROOT '{self.growi_content_root}' does not exist.")
        return self


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    return default if value in (None, "") else int(value)


def _parse_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _read_environment() -> dict[str, object]:
    env = os.environ
    return {
        "growi_base_url": env.get("GROWI_BASE_URL"),
        "growi_access_token": env.get("GROWI_ACCESS_TOKEN", ""),
        "growi_content_root": _parse_path(env.get("GROWI_CONTENT_ROOT")),
        "growi_timeout_ms": _parse_int(env.get("GROWI_TIMEOUT_MS"), 30_000),
        "growi_verify_tls": _parse_bool(env.get("GROWI_VERIFY_TLS"), True),
        "growi_enable_write_tools": _parse_bool(env.get("GROWI_ENABLE_WRITE_TOOLS"), False),
        "growi_user_agent": env.get("GROWI_USER_AGENT", "growi-mcp-server/0.1"),
        "mcp_transport": env.get("MCP_TRANSPORT", "stdio"),
        "mcp_http_host": env.get("MCP_HTTP_HOST", "127.0.0.1"),
        "mcp_http_port": _parse_int(env.get("MCP_HTTP_PORT"), 8787),
        "mcp_http_path": env.get("MCP_HTTP_PATH", "/mcp"),
        "log_level": env.get("LOG_LEVEL", "INFO"),
    }


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load settings from process environment and raise a domain-specific error on failure."""

    try:
        return Settings.model_validate(_read_environment())
    except (ValidationError, ValueError) as exc:
        raise ConfigurationError(str(exc)) from exc
