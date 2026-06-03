from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from growi_mcp_server.mcp_app.context import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(name="list_pages")
    async def list_pages(
        path: str,
        limit: int = 25,
        offset: int = 0,
    ) -> dict:
        """List GROWI pages under the given path prefix.

        Args:
            path: GROWI path prefix to list (e.g. ``/dev`` lists all pages under ``/dev``).
            limit: Maximum number of pages to return (1–100, default 25).
            offset: Pagination offset (default 0).

        Returns:
            Dict with ``pages`` (list of {id, path, status, updated_at}),
            ``total_count``, ``limit``, and ``offset``.
        """
        return await ctx.service.list_pages(path, limit=limit, offset=offset)

    @mcp.tool(name="get_page")
    async def get_page(
        page_id: str | None = None,
        path: str | None = None,
    ) -> dict | None:
        """Get a single GROWI page by ID or path.

        Provide either ``page_id`` or ``path`` (path takes precedence when both given).
        Returns ``null`` when the page does not exist.

        Returns:
            Dict with ``id``, ``path``, ``body``, ``revision_id``, ``creator``,
            ``last_update_user``, ``grant``, ``tags``, ``status``, timestamps.
        """
        return await ctx.service.get_page(page_id=page_id, path=path)

    @mcp.tool(name="search_pages")
    async def search_pages(
        q: str,
        limit: int = 20,
        offset: int = 0,
        path: str | None = None,
    ) -> dict:
        """Full-text search across GROWI pages.

        Args:
            q: Search query string.
            limit: Maximum number of results (default 20).
            offset: Pagination offset (default 0).
            path: Optional path prefix to restrict the search scope.

        Returns:
            Dict with ``hits`` (list of {id, path, snippet}), ``total``, ``query``.
        """
        return await ctx.service.search_pages(q, limit=limit, offset=offset, path=path)
