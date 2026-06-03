from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from growi_mcp_server.domain.services import GrowiService
from growi_mcp_server.mcp_app.context import AppContext
from growi_mcp_server.mcp_app.tools import deploy, pages_read, revisions, whoami
from growi_mcp_server.settings import Settings


def build_server(settings: Settings) -> FastMCP:
    """Construct the FastMCP server and register GROWI capabilities."""

    mcp = FastMCP(
        name="GROWI MCP Server",
        instructions=(
            "Deploy local Markdown files to GROWI and browse GROWI pages safely "
            "through the official GROWI REST API v3. "
            "Write operations (deploy_page) require GROWI_ENABLE_WRITE_TOOLS=true "
            "and only work on pages you created."
        ),
        json_response=True,
    )
    ctx = AppContext(settings=settings, service=GrowiService(settings))

    for module in (whoami, pages_read, revisions, deploy):
        module.register(mcp, ctx)

    return mcp
