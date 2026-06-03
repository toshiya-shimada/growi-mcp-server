from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from growi_mcp_server.mcp_app.context import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="whoami")
    async def whoami() -> dict:
        """Return the current authenticated GROWI user (id, username, name, email).

        Use this to confirm which account is connected and to understand
        which pages you are allowed to update via deploy_page.
        """
        return await ctx.service.whoami()
