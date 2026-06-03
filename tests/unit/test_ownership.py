from __future__ import annotations

import pytest

from growi_mcp_server.domain.models import CurrentUser, PageDetail, UserRef
from growi_mcp_server.domain.services import GrowiService
from growi_mcp_server.growi.errors import GrowiOwnershipError
from tests.helpers import make_settings


def _make_service() -> GrowiService:
    return GrowiService(make_settings())


def _make_page(creator_id: str = "u1", creator_username: str = "alice") -> PageDetail:
    return PageDetail(
        id="p1",
        path="/test",
        revision_id="r1",
        creator=UserRef(id=creator_id, username=creator_username),
    )


def _make_user(user_id: str = "u1", username: str = "alice") -> CurrentUser:
    return CurrentUser(id=user_id, username=username)


class TestAssertIsCreator:
    def test_owner_passes(self):
        svc = _make_service()
        page = _make_page(creator_id="u1")
        user = _make_user(user_id="u1")
        svc._assert_is_creator(page, user)  # should not raise

    def test_non_owner_raises(self):
        svc = _make_service()
        page = _make_page(creator_id="u1", creator_username="alice")
        user = _make_user(user_id="u2", username="bob")
        with pytest.raises(GrowiOwnershipError, match="alice"):
            svc._assert_is_creator(page, user)

    def test_no_creator_raises(self):
        svc = _make_service()
        page = PageDetail(id="p1", path="/test")  # no creator
        user = _make_user()
        with pytest.raises(GrowiOwnershipError, match="no creator"):
            svc._assert_is_creator(page, user)

    def test_same_id_different_username_passes(self):
        """ID equality is the deciding factor, not username."""
        svc = _make_service()
        page = _make_page(creator_id="u1", creator_username="old-name")
        user = _make_user(user_id="u1", username="new-name")
        svc._assert_is_creator(page, user)  # should not raise
