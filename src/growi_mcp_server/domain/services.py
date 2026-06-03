from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from growi_mcp_server.content.frontmatter import ParsedMarkdown, parse_frontmatter
from growi_mcp_server.content.loader import load_markdown_file
from growi_mcp_server.domain.mappers import (
    map_current_user,
    map_page_detail,
    map_page_summary,
    map_revision_detail,
    map_revision_summary,
    map_search_result,
)
from growi_mcp_server.domain.models import (
    CurrentUser,
    DeployResult,
    PageDetail,
    RevisionDetail,
    SearchResult,
)
from growi_mcp_server.growi.client import GrowiClient
from growi_mcp_server.growi.endpoints.page import PageEndpoint
from growi_mcp_server.growi.endpoints.pages import PagesEndpoint
from growi_mcp_server.growi.endpoints.personal_setting import PersonalSettingEndpoint
from growi_mcp_server.growi.endpoints.revisions import RevisionsEndpoint
from growi_mcp_server.growi.endpoints.search import SearchEndpoint
from growi_mcp_server.growi.errors import (
    GrowiNotFoundError,
    GrowiOwnershipError,
    GrowiValidationError,
)
from growi_mcp_server.settings import Settings

LOGGER = logging.getLogger(__name__)


class GrowiService:
    """High-level orchestration layer between MCP tool handlers and GROWI endpoints.

    Applies business rules:
    - Write tools must be explicitly enabled via ``GROWI_ENABLE_WRITE_TOOLS``.
    - Page updates verify that the current user is the page creator (strict match).
    - No delete / move / rename operations are exposed.
    """

    def __init__(self, settings: Settings, client: GrowiClient | None = None) -> None:
        self.settings = settings
        self.client = client or GrowiClient(settings)
        self.personal_setting = PersonalSettingEndpoint(self.client)
        self.page_ep = PageEndpoint(self.client)
        self.pages_ep = PagesEndpoint(self.client)
        self.search_ep = SearchEndpoint(self.client)
        self.revisions_ep = RevisionsEndpoint(self.client)

    async def aclose(self) -> None:
        await self.client.aclose()

    # ──────────────────────────────────────────────
    # Guards
    # ──────────────────────────────────────────────

    def _require_write_enabled(self) -> None:
        """Raise if write tools are not enabled."""
        if not self.settings.growi_enable_write_tools:
            raise GrowiValidationError(
                "Write tools are disabled. Set GROWI_ENABLE_WRITE_TOOLS=true to enable deploy_page."
            )

    def _require_content_root(self) -> Path:
        """Return the configured content root or raise if not set."""
        if not self.settings.growi_content_root:
            raise GrowiValidationError(
                "GROWI_CONTENT_ROOT must be set for file-based operations "
                "(deploy_page, preview_frontmatter)."
            )
        return self.settings.growi_content_root

    def _assert_is_creator(self, page: PageDetail, current_user: CurrentUser) -> None:
        """Raise :class:`GrowiOwnershipError` when the current user did not create the page."""
        creator = page.creator
        if creator is None:
            raise GrowiOwnershipError(
                f"Page '{page.path}' has no creator information. "
                "Cannot verify ownership; update blocked for safety."
            )
        if creator.id != current_user.id:
            raise GrowiOwnershipError(
                f"Page '{page.path}' was created by '{creator.username or creator.id}', "
                f"but you are '{current_user.username}'. "
                "Only the page creator may update this page via growi-mcp-server."
            )

    # ──────────────────────────────────────────────
    # Read operations (no ownership restriction)
    # ──────────────────────────────────────────────

    async def whoami(self) -> dict[str, Any]:
        """Return the current authenticated GROWI user."""
        payload = await self.personal_setting.get_current_user()
        user = map_current_user(payload)
        return user.model_dump()

    async def get_page(
        self,
        *,
        page_id: str | None = None,
        path: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a single page by ID or path.

        Returns ``None`` when the page is not found (404).
        Raises for all other errors.
        """
        try:
            payload = await self.page_ep.get(page_id=page_id, path=path)
        except GrowiNotFoundError:
            return None
        page = map_page_detail(payload)
        return page.model_dump()

    async def get_page_or_raise(
        self,
        *,
        page_id: str | None = None,
        path: str | None = None,
    ) -> PageDetail:
        """Get a page and raise ``GrowiNotFoundError`` when not found."""
        payload = await self.page_ep.get(page_id=page_id, path=path)
        return map_page_detail(payload)

    async def list_pages(
        self,
        path: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List pages under the given path prefix."""
        if limit <= 0:
            raise GrowiValidationError("limit must be positive.")
        if limit > 100:
            raise GrowiValidationError("limit must be <= 100.")
        payload = await self.pages_ep.list(path, limit=limit, offset=offset)
        pages = [map_page_summary(p) for p in (payload.get("pages") or [])]
        summaries = [s.model_dump() for s in pages]
        return {
            "pages": summaries,
            "total_count": payload.get("totalCount"),
            "limit": limit,
            "offset": offset,
        }

    async def search_pages(
        self,
        q: str,
        *,
        limit: int = 20,
        offset: int = 0,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Full-text search across GROWI pages."""
        if not q.strip():
            raise GrowiValidationError("Search query must not be empty.")
        payload = await self.search_ep.search(q, limit=limit, offset=offset, path=path)
        result: SearchResult = map_search_result(payload, query=q)
        return result.model_dump()

    async def list_page_revisions(
        self,
        page_id: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List revision history for a page."""
        payload = await self.revisions_ep.list(page_id, limit=limit, offset=offset)
        revisions = [map_revision_summary(r).model_dump() for r in (payload.get("revisions") or [])]
        return {
            "revisions": revisions,
            "total_count": payload.get("totalCount"),
            "limit": limit,
            "offset": offset,
        }

    async def get_revision(self, revision_id: str) -> dict[str, Any]:
        """Get a single revision by ID."""
        payload = await self.revisions_ep.get(revision_id)
        rev: RevisionDetail = map_revision_detail(payload)
        return rev.model_dump()

    # ──────────────────────────────────────────────
    # Content-root helpers (local file operations)
    # ──────────────────────────────────────────────

    async def preview_frontmatter(self, file_path: str) -> dict[str, Any]:
        """Parse and return front-matter metadata from a local Markdown file.

        Does **not** communicate with GROWI; purely local.
        """
        root = self._require_content_root()
        raw = load_markdown_file(file_path, root)
        parsed = parse_frontmatter(raw)
        return {
            "growi_path": parsed.meta.growi_path,
            "grant": parsed.meta.grant,
            "tags": parsed.meta.tags,
            "body_preview": parsed.body[:200] + ("..." if len(parsed.body) > 200 else ""),
            "body_length": len(parsed.body),
        }

    # ──────────────────────────────────────────────
    # Internal write helpers
    # ──────────────────────────────────────────────

    async def _create_page(
        self,
        *,
        path: str,
        body: str,
        grant: int | None,
        tags: list[str],
    ) -> PageDetail:
        payload = await self.page_ep.create(
            path=path,
            body=body,
            grant=grant,
            tags=tags if tags else None,
        )
        return map_page_detail(payload)

    async def _update_page(
        self,
        *,
        page_id: str,
        revision_id: str,
        body: str,
    ) -> PageDetail:
        payload = await self.page_ep.update(
            page_id=page_id,
            revision_id=revision_id,
            body=body,
        )
        return map_page_detail(payload)

    # ──────────────────────────────────────────────
    # Deploy (main public write operation)
    # ──────────────────────────────────────────────

    async def deploy_page(
        self,
        file_path: str,
        *,
        dry_run: bool = False,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        """Deploy a local Markdown file to GROWI.

        Flow:
        1. Validate that write tools are enabled.
        2. Load the file from ``GROWI_CONTENT_ROOT`` (path-traversal safe).
        3. Parse YAML front-matter to extract ``growi_path``, ``grant``, ``tags``.
        4. Fetch the current authenticated user (for ownership verification).
        5. Try to fetch the target GROWI page:
           - **Not found** → create the page (current user becomes creator).
           - **Found, creator matches** → update the page with the new body.
           - **Found, creator differs** → raise ``GrowiOwnershipError``.
        6. If ``dry_run=True``, skip step 5's write and return a preview.

        Args:
            file_path: Path to the Markdown file to deploy.
            dry_run: If ``True``, return the planned action without writing.
            base_url: GROWI base URL for constructing the page URL in the result.

        Returns:
            A :class:`DeployResult`-shaped dict.
        """
        self._require_write_enabled()
        root = self._require_content_root()

        # 1. Load and parse the file
        raw = load_markdown_file(file_path, root)
        parsed: ParsedMarkdown = parse_frontmatter(raw)
        growi_path = parsed.meta.growi_path

        # 2. Get current user (for ownership check)
        me_payload = await self.personal_setting.get_current_user()
        current_user: CurrentUser = map_current_user(me_payload)

        # 3. Check whether the page already exists
        try:
            existing_payload = await self.page_ep.get(path=growi_path)
            existing: PageDetail | None = map_page_detail(existing_payload)
        except GrowiNotFoundError:
            existing = None

        _base = (base_url or str(self.settings.growi_base_url)).rstrip("/")

        if existing is None:
            # Page does not exist → create
            if dry_run:
                LOGGER.info("dry_run: would create page at '%s'", growi_path)
                result = DeployResult(
                    action="dry_run",
                    target_path=growi_path,
                    dry_run=True,
                    ownership_ok=True,
                    would_action="create",
                )
                return result.model_dump()

            created = await self._create_page(
                path=growi_path,
                body=parsed.body,
                grant=parsed.meta.grant,
                tags=parsed.meta.tags,
            )
            LOGGER.info("created page '%s' (id=%s)", growi_path, created.id)
            return DeployResult(
                action="created",
                target_path=growi_path,
                page_id=created.id,
                revision_id=created.revision_id,
                url=f"{_base}{growi_path}",
                dry_run=False,
                ownership_ok=True,
            ).model_dump()

        # Page exists → ownership check
        try:
            self._assert_is_creator(existing, current_user)
        except GrowiOwnershipError:
            if dry_run:
                LOGGER.info("dry_run: would block update of '%s' (creator mismatch)", growi_path)
                return DeployResult(
                    action="dry_run",
                    target_path=growi_path,
                    page_id=existing.id,
                    dry_run=True,
                    ownership_ok=False,
                    would_action="blocked",
                ).model_dump()
            raise

        if dry_run:
            LOGGER.info("dry_run: would update page at '%s' (id=%s)", growi_path, existing.id)
            return DeployResult(
                action="dry_run",
                target_path=growi_path,
                page_id=existing.id,
                revision_id=existing.revision_id,
                dry_run=True,
                ownership_ok=True,
                would_action="update",
            ).model_dump()

        revision_id = existing.revision_id or ""
        updated = await self._update_page(
            page_id=existing.id,
            revision_id=revision_id,
            body=parsed.body,
        )
        LOGGER.info("updated page '%s' (id=%s)", growi_path, updated.id)
        return DeployResult(
            action="updated",
            target_path=growi_path,
            page_id=updated.id,
            revision_id=updated.revision_id,
            url=f"{_base}{growi_path}",
            dry_run=False,
            ownership_ok=True,
        ).model_dump()
