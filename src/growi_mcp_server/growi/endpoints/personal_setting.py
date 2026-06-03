from __future__ import annotations

from typing import Any

from growi_mcp_server.growi.client import GrowiClient


class PersonalSettingEndpoint:
    """Wraps GET /_api/v3/personal-setting/ to retrieve the current user."""

    def __init__(self, client: GrowiClient) -> None:
        self._client = client

    async def get_current_user(self) -> dict[str, Any]:
        """Return the ``currentUser`` object from personal-setting.

        Response shape::

            {"currentUser": {"_id": "...", "username": "...", "name": "...", "email": "..."}}
        """
        return await self._client.request_json("GET", "/_api/v3/personal-setting/")
