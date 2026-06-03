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

MD_CONTENT = "---\ngrowi_path: /test/page\n---\n# Hello\nWorld"


@pytest.fixture
def content_root(tmp_path):
    md = tmp_path / "page.md"
    md.write_text(MD_CONTENT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def md_path(content_root):
    return str(content_root / "page.md")


@pytest.fixture
def settings_write(content_root):
    return make_settings(write=True, content_root=content_root)


@pytest.fixture
def settings_no_write(content_root):
    return make_settings(write=False, content_root=content_root)


async def test_deploy_page_not_registered_when_write_disabled(settings_no_write):
    server = build_server(settings_no_write)
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert "deploy_page" not in names


async def test_deploy_page_registered_when_write_enabled(settings_write):
    server = build_server(settings_write)
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert "deploy_page" in names


async def test_preview_frontmatter_always_registered(settings_no_write):
    server = build_server(settings_no_write)
    tools = await server.list_tools()
    names = {t.name for t in tools}
    assert "preview_frontmatter" in names


@respx.mock
async def test_preview_frontmatter(settings_write, md_path):
    server = build_server(settings_write)
    result = await server.call_tool("preview_frontmatter", {"file_path": md_path})
    data = decode_tool_result(result)
    assert data["growi_path"] == "/test/page"
    assert "Hello" in data["body_preview"]


@respx.mock
async def test_deploy_page_creates_new_page(settings_write, md_path):
    """When page does not exist (404), deploy_page should POST to create it."""
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(200, json=make_current_user_payload())
    )
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(404, json={"errors": ["page not found"]})
    )
    create_route = respx.post("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(201, json=make_page_payload())
    )

    server = build_server(settings_write)
    result = await server.call_tool("deploy_page", {"file_path": md_path})
    data = decode_tool_result(result)

    assert data["action"] == "created"
    assert data["target_path"] == "/test/page"
    assert data["page_id"] == "p1"
    assert create_route.called


@respx.mock
async def test_deploy_page_updates_own_page(settings_write, md_path):
    """When page exists and creator matches, deploy_page should PUT to update."""
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(200, json=make_current_user_payload(user_id="user1"))
    )
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(200, json=make_page_payload(creator_id="user1"))
    )
    update_route = respx.put("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(
            200, json=make_page_payload(revision_id="r2", creator_id="user1")
        )
    )

    server = build_server(settings_write)
    result = await server.call_tool("deploy_page", {"file_path": md_path})
    data = decode_tool_result(result)

    assert data["action"] == "updated"
    assert update_route.called


@respx.mock
async def test_deploy_page_blocks_other_owners_page(settings_write, md_path):
    """When page creator differs from current user, deploy_page must raise GrowiOwnershipError."""
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(
            200, json=make_current_user_payload(user_id="user2", username="bob")
        )
    )
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(
            200, json=make_page_payload(creator_id="user1", creator_username="alice")
        )
    )
    put_route = respx.put("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(200, json={})
    )

    server = build_server(settings_write)
    with pytest.raises(Exception, match="alice"):
        await server.call_tool("deploy_page", {"file_path": md_path})

    # PUT must NOT have been called
    assert not put_route.called


@respx.mock
async def test_deploy_page_dry_run_create(settings_write, md_path):
    """dry_run=True when page doesn't exist should return would_action=create without POST."""
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(200, json=make_current_user_payload())
    )
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(404, json={"errors": ["not found"]})
    )
    post_route = respx.post("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(201, json={})
    )

    server = build_server(settings_write)
    result = await server.call_tool("deploy_page", {"file_path": md_path, "dry_run": True})
    data = decode_tool_result(result)

    assert data["action"] == "dry_run"
    assert data["would_action"] == "create"
    assert data["dry_run"] is True
    assert not post_route.called


@respx.mock
async def test_deploy_page_dry_run_blocked(settings_write, md_path):
    """dry_run=True when creator mismatches should return would_action=blocked without PUT."""
    respx.get("http://growi.test/_api/v3/personal-setting/").mock(
        return_value=httpx.Response(200, json=make_current_user_payload(user_id="user2"))
    )
    respx.get("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(200, json=make_page_payload(creator_id="user1"))
    )
    put_route = respx.put("http://growi.test/_api/v3/page").mock(
        return_value=httpx.Response(200, json={})
    )

    server = build_server(settings_write)
    result = await server.call_tool("deploy_page", {"file_path": md_path, "dry_run": True})
    data = decode_tool_result(result)

    assert data["action"] == "dry_run"
    assert data["would_action"] == "blocked"
    assert data["ownership_ok"] is False
    assert not put_route.called
