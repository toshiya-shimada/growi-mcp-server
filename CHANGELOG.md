# Changelog

## [0.1.0] - 2026-06-03

### Added
- Initial release.
- `whoami` tool: return the current authenticated GROWI user.
- `list_pages` tool: list pages under a given path.
- `get_page` tool: get page details including body, creator, and revision info.
- `search_pages` tool: full-text search across GROWI pages.
- `list_page_revisions` tool: list revision history for a page.
- `get_revision` tool: get a single revision by ID.
- `preview_frontmatter` tool: parse and preview YAML front-matter from a local Markdown file.
- `deploy_page` tool (write, opt-in): deploy a local Markdown file to GROWI.
  - Reads `growi_path` from YAML front-matter.
  - Creates the page if it does not exist.
  - Updates the page if it exists and the current user is the creator.
  - Blocks update if the current user is not the page creator.
  - Supports `dry_run=true` for safe preview without any write operations.
