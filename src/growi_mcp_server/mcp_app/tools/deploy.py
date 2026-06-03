from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from growi_mcp_server.mcp_app.context import AppContext


def register(mcp: FastMCP, ctx: AppContext) -> None:
    """Register file-based deploy tools.

    ``preview_frontmatter`` is always registered (read-only, needs GROWI_CONTENT_ROOT).
    ``deploy_page`` is only registered when ``GROWI_ENABLE_WRITE_TOOLS=true``.
    """

    @mcp.tool(name="preview_frontmatter")
    async def preview_frontmatter(file_path: str) -> dict:
        """Parse and preview the YAML front-matter of a local Markdown file.

        Reads the file from ``GROWI_CONTENT_ROOT`` and returns the parsed
        metadata without communicating with GROWI.  Use this to verify
        that ``growi_path``, ``grant``, and ``tags`` are correct before
        running ``deploy_page``.

        Args:
            file_path: Absolute or relative path to the Markdown file.
                       Must be within ``GROWI_CONTENT_ROOT``.

        Returns:
            Dict with ``growi_path``, ``grant``, ``tags``,
            ``body_preview`` (first 200 chars), and ``body_length``.
        """
        return await ctx.service.preview_frontmatter(file_path)

    if ctx.settings.growi_enable_write_tools:

        @mcp.tool(name="deploy_page")
        async def deploy_page(
            file_path: str,
            dry_run: bool = False,
        ) -> dict:
            """Deploy a local Markdown file to GROWI.

            Reads the file from ``GROWI_CONTENT_ROOT``, parses the YAML
            front-matter to determine the destination GROWI path, then:

            - Creates the page if it does not exist yet.
            - Updates the page if it exists **and** the current user is
              the page creator.
            - **Blocks** the update if the page was created by someone else.

            The Markdown body sent to GROWI is the content *after* the
            front-matter block (the ``---`` delimiters are stripped).

            Safety:
            - No delete / rename operations are ever performed.
            - Only files within ``GROWI_CONTENT_ROOT`` can be read.
            - Ownership is verified before any write.

            Front-matter format::

                ---
                growi_path: /your/page/path   # required
                grant: 1                       # optional (1=public, 2=restricted …)
                tags: [tag1, tag2]             # optional
                ---

                # Markdown body starts here

            Args:
                file_path: Path to the Markdown file to deploy.
                           Must be within ``GROWI_CONTENT_ROOT``.
                dry_run: If ``true``, return the planned action
                         (create / update / blocked) without writing anything.

            Returns:
                Dict with ``action`` (created | updated | dry_run),
                ``target_path``, ``page_id``, ``revision_id``, ``url``,
                ``dry_run``, ``ownership_ok``, and ``would_action``
                (only set in dry_run mode).
            """
            base_url = str(ctx.settings.growi_base_url).rstrip("/")
            return await ctx.service.deploy_page(
                file_path,
                dry_run=dry_run,
                base_url=base_url,
            )
