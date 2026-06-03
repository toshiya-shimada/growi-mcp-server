from __future__ import annotations

from typing import Any

from growi_mcp_server.growi.client import GrowiClient


class SearchEndpoint:
    """Wraps GET /_api/v3/search for full-text page search."""

    def __init__(self, client: GrowiClient) -> None:
        self._client = client

    async def search(
        self,
        q: str,
        *,
        limit: int = 20,
        offset: int = 0,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Full-text search across GROWI pages.

        Response shape varies by GROWI version; the raw ``data`` object is returned.
        """
        params: dict[str, Any] = {"q": q, "limit": limit, "offset": offset}
        if path:
            params["path"] = path
        return await self._client.request_json("GET", "/_api/v3/search", params=params)
