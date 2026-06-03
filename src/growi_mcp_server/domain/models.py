from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DomainModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class UserRef(DomainModel):
    """Lightweight user reference embedded in page objects."""

    id: str
    username: str | None = None
    name: str | None = None


class CurrentUser(DomainModel):
    """The authenticated user returned by personal-setting."""

    id: str
    username: str
    name: str | None = None
    email: str | None = None


class PageSummary(DomainModel):
    """Lightweight page entry from list endpoints."""

    id: str
    path: str
    status: str | None = None
    updated_at: datetime | None = None


class RevisionSummary(DomainModel):
    """Lightweight revision entry from revisions/list."""

    id: str
    author: UserRef | None = None
    created_at: datetime | None = None


class PageDetail(DomainModel):
    """Full page details including body and revision."""

    id: str
    path: str
    body: str | None = None
    revision_id: str | None = None
    creator: UserRef | None = None
    last_update_user: UserRef | None = None
    grant: int | None = None
    tags: list[str] = Field(default_factory=list)
    status: str | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None


class RevisionDetail(DomainModel):
    """Full revision with body."""

    id: str
    body: str | None = None
    format: str | None = None
    author: UserRef | None = None
    created_at: datetime | None = None


class SearchHit(DomainModel):
    """A single search result."""

    id: str | None = None
    path: str | None = None
    snippet: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class SearchResult(DomainModel):
    """Search response."""

    hits: list[SearchHit] = Field(default_factory=list)
    total: int | None = None
    query: str | None = None


class DeployResult(DomainModel):
    """Result of a deploy_page operation."""

    action: Literal["created", "updated", "dry_run"]
    target_path: str
    page_id: str | None = None
    revision_id: str | None = None
    url: str | None = None
    dry_run: bool = False
    ownership_ok: bool | None = None
    # In dry_run mode, would_action indicates what would have happened
    would_action: Literal["create", "update", "blocked"] | None = None
