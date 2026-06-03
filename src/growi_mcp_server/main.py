from __future__ import annotations

from growi_mcp_server.mcp_app.server import build_server
from growi_mcp_server.settings import load_settings
from growi_mcp_server.utils.logging import configure_logging


def main() -> None:
    """Process entrypoint."""

    settings = load_settings()
    configure_logging(settings.log_level)
    server = build_server(settings)

    if settings.mcp_transport == "stdio":
        server.run(transport="stdio")
        return

    if settings.mcp_transport == "streamable-http":
        server.run(transport="streamable-http")
        return

    raise ValueError(f"Unsupported transport: {settings.mcp_transport}")
