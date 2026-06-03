from __future__ import annotations

from typing import Any

from growi_mcp_server.growi.client import GrowiClient


class RevisionsEndpoint:
    """Wraps /_api/v3/revisions/* for page revision history."""

    def __init__(self, client: GrowiClient) -> None:
        self._client = client

    async def list(
        self,
        page_id: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List revisions for a page.

        Response shape::

            {"revisions": [{"_id": "...", "author": {...}, "createdAt": "..."}], "totalCount": N}
        """
        params: dict[str, Any] = {"pageId": page_id, "limit": limit, "offset": offset}
        return await self._client.request_json("GET", "/_api/v3/revisions/list", params=params)

    async def get(self, revision_id: str) -> dict[str, Any]:
        """Get a single revision by ID.

        Response shape::

            {"revision": {"_id": "...", "body": "...", "format": "markdown", "author": {...}}}
        """
        return await self._client.request_json("GET", f"/_api/v3/revisions/{revision_id}")
