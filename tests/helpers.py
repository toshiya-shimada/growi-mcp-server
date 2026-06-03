from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.types import TextContent

from growi_mcp_server.settings import Settings


def make_settings(
    *,
    write: bool = False,
    content_root: Path | None = None,
    base_url: str = "http://growi.test",
    token: str = "test-token",
) -> Settings:
    """Build a :class:`Settings` object suitable for tests."""
    return Settings(
        growi_base_url=base_url,  # type: ignore[arg-type]
        growi_access_token=token,
        growi_content_root=content_root,
        growi_enable_write_tools=write,
    )


def decode_tool_result(result: Any) -> Any:
    """Extract and JSON-decode the text payload from an MCP tool result.

    FastMCP returns a tuple ``(content_list, metadata_dict)``.
    - content_list is empty when the tool returned ``None``.
    - Otherwise content_list[0].text holds the JSON-encoded value.
    """
    # Unwrap tuple format returned by FastMCP.call_tool
    if isinstance(result, tuple):
        content_list: list[Any] = result[0] if result else []
        metadata: dict[str, Any] = result[1] if len(result) > 1 else {}
        if not content_list:
            # Tool returned None
            return metadata.get("result", None)
        result = content_list

    if isinstance(result, list):
        for item in result:
            if isinstance(item, TextContent):
                return json.loads(item.text)
    if isinstance(result, TextContent):
        return json.loads(result.text)
    return result


def make_page_payload(
    *,
    page_id: str = "p1",
    path: str = "/test/page",
    creator_id: str = "user1",
    creator_username: str = "alice",
    revision_id: str = "r1",
    body: str = "# Test",
) -> dict[str, Any]:
    """Build a minimal GROWI page API response payload."""
    return {
        "page": {
            "_id": page_id,
            "path": path,
            "creator": {"_id": creator_id, "username": creator_username, "name": "Alice"},
            "lastUpdateUser": {"_id": creator_id, "username": creator_username, "name": "Alice"},
            "revision": {"_id": revision_id, "body": body},
            "grant": 1,
            "status": "published",
        }
    }


def make_current_user_payload(
    *,
    user_id: str = "user1",
    username: str = "alice",
    name: str = "Alice",
) -> dict[str, Any]:
    """Build a minimal GROWI personal-setting response payload."""
    return {
        "currentUser": {
            "_id": user_id,
            "username": username,
            "name": name,
            "email": f"{username}@example.com",
        }
    }
