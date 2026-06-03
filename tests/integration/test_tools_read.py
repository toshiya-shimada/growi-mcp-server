from __future__ import annotations

import httpx
import pytest
import respx

from growi_mcp_server.mcp_app.server import build_server
from tests.helpers import (
    decode_tool_result,
    make_current_user_payload,
    make_page_payload,
    make_settings,
)


@pytest.fixture
def settings():
    return make_settings()


@respx.mock
async def test_whoami_returns_current_user(settings):
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(200, json=make_current_user_payload())
    )
    server = build_server(settings)
    result = await server.call_tool("whoami", {})
    data = decode_tool_result(result)
    assert data["username"] == "alice"
    assert data["id"] == "user1"


@respx.mock
async def test_get_page_returns_page_detail(settings):
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(200, json=make_page_payload(path="/docs/api"))
    )
    server = build_server(settings)
    result = await server.call_tool("get_page", {"path": "/docs/api"})
    data = decode_tool_result(result)
    assert data["path"] == "/docs/api"
    assert data["revision_id"] == "r1"
    assert data["creator"]["username"] == "alice"


@respx.mock
async def test_get_page_returns_none_on_404(settings):
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(404, json={"errors": ["page not found"]})
    )
    server = build_server(settings)
    result = await server.call_tool("get_page", {"path": "/nonexistent"})
    data = decode_tool_result(result)
    assert data is None


@respx.mock
async def test_list_pages(settings):
    respx.get("http://growi.test/_api/v3/pages/list").mock(
        return_value=httpx.Response(
            200,
            json={
                "pages": [
                    {"_id": "p1", "path": "/docs/a"},
                    {"_id": "p2", "path": "/docs/b"},
                ],
                "totalCount": 2,
            },
        )
    )
    server = build_server(settings)
    result = await server.call_tool("list_pages", {"path": "/docs"})
    data = decode_tool_result(result)
    assert len(data["pages"]) == 2
    assert data["pages"][0]["path"] == "/docs/a"


@respx.mock
async def test_search_pages(settings):
    respx.get("http://growi.test/_api/v3/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "body": [{"_source": {"_id": "p1", "path": "/docs/api", "body": "API docs"}}],
                    "total": 1,
                }
            },
        )
    )
    server = build_server(settings)
    result = await server.call_tool("search_pages", {"q": "API"})
    data = decode_tool_result(result)
    assert data["query"] == "API"
    assert data["total"] == 1


@respx.mock
async def test_list_page_revisions(settings):
    respx.get("http://growi.test/_api/v3/revisions/list").mock(
        return_value=httpx.Response(
            200,
            json={
                "revisions": [{"_id": "r2"}, {"_id": "r1"}],
                "totalCount": 2,
            },
        )
    )
    server = build_server(settings)
    result = await server.call_tool("list_page_revisions", {"page_id": "p1"})
    data = decode_tool_result(result)
    assert len(data["revisions"]) == 2


@respx.mock
async def test_get_revision(settings):
    respx.get("http://growi.test/_api/v3/revisions/r1").mock(
        return_value=httpx.Response(
            200,
            json={"revision": {"_id": "r1", "body": "# Hello", "format": "markdown"}},
        )
    )
    server = build_server(settings)
    result = await server.call_tool("get_revision", {"revision_id": "r1"})
    data = decode_tool_result(result)
    assert data["id"] == "r1"
    assert data["body"] == "# Hello"


async def test_delete_tools_not_registered(settings):
    """Deletion and rename tools must never appear in the tool list."""
    server = build_server(settings)
    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    for forbidden in ("delete_page", "rename_page", "move_page", "empty_trash"):
        assert forbidden not in tool_names, f"Forbidden tool registered: {forbidden}"
