from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from growi_mcp_server.mcp_app.context import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="list_page_revisions")
    async def list_page_revisions(
        page_id: str,
        limit: int = 25,
        offset: int = 0,
    ) -> dict:
        """List the revision history of a GROWI page.

        Args:
            page_id: GROWI page ID (``_id`` from get_page or list_pages).
            limit: Maximum number of revisions to return (default 25).
            offset: Pagination offset (default 0).

        Returns:
            Dict with ``revisions`` (list of {id, author, created_at}),
            ``total_count``, ``limit``, and ``offset``.
        """
        return await ctx.service.list_page_revisions(page_id, limit=limit, offset=offset)

    @mcp.tool(name="get_revision")
    async def get_revision(revision_id: str) -> dict:
        """Get a single GROWI page revision by its ID.

        Args:
            revision_id: Revision ID (``_id`` from list_page_revisions or get_page).

        Returns:
            Dict with ``id``, ``body``, ``format``, ``author``, ``created_at``.
        """
        return await ctx.service.get_revision(revision_id)
