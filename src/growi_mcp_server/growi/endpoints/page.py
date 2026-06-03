from __future__ import annotations

from typing import Any

from growi_mcp_server.growi.client import GrowiClient


class PageEndpoint:
    """Wraps GET / POST / PUT /_api/v3/page for single-page operations."""

    def __init__(self, client: GrowiClient) -> None:
        self._client = client

    async def get(
        self,
        *,
        page_id: str | None = None,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve a single page by ``pageId`` or ``path``.

        Response shape::

            {
              "page": {
                "_id": "...",
                "path": "/...",
                "creator": {"_id": "...", "username": "...", "name": "..."},
                "lastUpdateUser": {"_id": "...", "username": "...", "name": "..."},
                "revision": {"_id": "...", "body": "..."},
                "grant": 1,
                "status": "published"
              }
            }
        """
        params: dict[str, Any] = {}
        if page_id:
            params["pageId"] = page_id
        if path:
            params["path"] = path
        return await self._client.request_json("GET", "/_api/v3/page", params=params)

    async def create(
        self,
        *,
        path: str,
        body: str,
        grant: int | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new page at the given path.

        Response shape (HTTP 201)::

            {"page": {"_id": "...", "path": "/...", "revision": {"_id": "..."}, ...}}
        """
        form: dict[str, Any] = {"path": path, "body": body}
        if grant is not None:
            form["grant"] = grant
        if tags:
            # GROWI accepts pageTags as a JSON array string
            import json

            form["pageTags"] = json.dumps(tags)
        return await self._client.request_json(
            "POST", "/_api/v3/page", form_data=form, accepted_statuses={200, 201}
        )

    async def update(
        self,
        *,
        page_id: str,
        revision_id: str,
        body: str,
    ) -> dict[str, Any]:
        """Update an existing page's body.

        Note: The parameter is ``revisionId`` (camelCase), not ``revision_id``.

        Response shape::

            {"page": {"_id": "...", "path": "/...", "revision": {"_id": "..."}, ...}}
        """
        form: dict[str, Any] = {
            "pageId": page_id,
            "revisionId": revision_id,
            "body": body,
        }
        return await self._client.request_json("PUT", "/_api/v3/page", form_data=form)
