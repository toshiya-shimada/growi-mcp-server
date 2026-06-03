from __future__ import annotations

from typing import Any

from growi_mcp_server.growi.client import GrowiClient


class PagesEndpoint:
    """Wraps /_api/v3/pages/* for multi-page listing operations."""

    def __init__(self, client: GrowiClient) -> None:
        self._client = client

    async def list(
        self,
        path: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List pages under the given path.

        Response shape::

            {"pages": [{"_id": "...", "path": "/..."}], "totalCount": N, "limit": N, "offset": N}
        """
        params: dict[str, Any] = {"path": path, "limit": limit, "offset": offset}
        return await self._client.request_json("GET", "/_api/v3/pages/list", params=params)
