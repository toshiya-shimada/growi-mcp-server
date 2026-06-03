from __future__ import annotations

from datetime import datetime
from typing import Any

from growi_mcp_server.domain.models import (
    CurrentUser,
    PageDetail,
    PageSummary,
    RevisionDetail,
    RevisionSummary,
    SearchHit,
    SearchResult,
    UserRef,
)


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _map_user_ref(raw: dict[str, Any] | None) -> UserRef | None:
    if not raw:
        return None
    return UserRef(
        id=str(raw.get("_id", "")),
        username=raw.get("username"),
        name=raw.get("name"),
    )


def map_current_user(payload: dict[str, Any]) -> CurrentUser:
    """Map personal-setting response to :class:`CurrentUser`."""

    raw = payload.get("currentUser") or payload
    return CurrentUser(
        id=str(raw.get("_id", "")),
        username=raw.get("username", ""),
        name=raw.get("name"),
        email=raw.get("email"),
    )


def map_page_detail(payload: dict[str, Any]) -> PageDetail:
    """Map a single-page API response to :class:`PageDetail`."""

    raw = payload.get("page") or payload
    revision_raw: dict[str, Any] = raw.get("revision") or {}
    tag_names: list[Any] = raw.get("tagNames") or raw.get("tags") or []

    return PageDetail(
        id=str(raw.get("_id", "")),
        path=str(raw.get("path", "")),
        body=revision_raw.get("body"),
        revision_id=str(revision_raw["_id"]) if revision_raw.get("_id") else None,
        creator=_map_user_ref(raw.get("creator")),
        last_update_user=_map_user_ref(raw.get("lastUpdateUser")),
        grant=raw.get("grant"),
        tags=[str(t) for t in tag_names],
        status=raw.get("status"),
        updated_at=_parse_dt(raw.get("updatedAt")),
        created_at=_parse_dt(raw.get("createdAt")),
    )


def map_page_summary(raw: dict[str, Any]) -> PageSummary:
    """Map a single entry from pages/list to :class:`PageSummary`."""

    return PageSummary(
        id=str(raw.get("_id", "")),
        path=str(raw.get("path", "")),
        status=raw.get("status"),
        updated_at=_parse_dt(raw.get("updatedAt")),
    )


def map_revision_summary(raw: dict[str, Any]) -> RevisionSummary:
    """Map a single entry from revisions/list to :class:`RevisionSummary`."""

    return RevisionSummary(
        id=str(raw.get("_id", "")),
        author=_map_user_ref(raw.get("author")),
        created_at=_parse_dt(raw.get("createdAt")),
    )


def map_revision_detail(payload: dict[str, Any]) -> RevisionDetail:
    """Map a single-revision response to :class:`RevisionDetail`."""

    raw = payload.get("revision") or payload
    return RevisionDetail(
        id=str(raw.get("_id", "")),
        body=raw.get("body"),
        format=raw.get("format"),
        author=_map_user_ref(raw.get("author")),
        created_at=_parse_dt(raw.get("createdAt")),
    )


def map_search_result(payload: dict[str, Any], query: str) -> SearchResult:
    """Map a search API response to :class:`SearchResult`.

    GROWI search response shape varies by version.  We handle common layouts
    defensively and fall back gracefully when the shape is unfamiliar.
    """

    data: dict[str, Any] = payload.get("data") or payload

    # Layout A: {"data": {"body": [...docs...], "total": N}}
    body = data.get("body")
    total: int | None = None

    if isinstance(body, list):
        docs = body
        total_raw = data.get("total") or data.get("totalCount")
        total = int(total_raw) if total_raw is not None else None
    elif isinstance(body, dict):
        # Layout B: {"data": {"body": {"docs": [...], "total": N}}}
        docs = body.get("docs") or []
        total_raw = body.get("total") or body.get("totalCount")
        total = int(total_raw) if total_raw is not None else None
    else:
        # Fallback: look for "pages" or "docs" at data level
        docs = data.get("docs") or data.get("pages") or []
        total_raw = data.get("total") or data.get("totalCount")
        total = int(total_raw) if total_raw is not None else None

    hits: list[SearchHit] = []
    for doc in docs:
        source: dict[str, Any] = doc.get("_source") or doc
        hits.append(
            SearchHit(
                id=str(source.get("_id") or doc.get("_id") or ""),
                path=source.get("path") or doc.get("path"),
                snippet=source.get("snippet") or source.get("body", "")[:200],
                extra={},
            )
        )

    return SearchResult(hits=hits, total=total, query=query)
