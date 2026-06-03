# growi-mcp-server

MIT-licensed [MCP](https://modelcontextprotocol.io) server that lets you deploy local Markdown files to [GROWI](https://growi.org/) and browse GROWI pages — all from Claude Code or any MCP-compatible client.

## Motivation

The primary use case is replacing the manual "copy-paste to GROWI" step in a local-git-managed wiki workflow:

1. Edit Markdown locally, commit with `git`.
2. Ask Claude Code to `deploy_page` — the server reads the file, parses the front-matter, and calls the GROWI API automatically.

## Safety guarantees

| Rule | Detail |
|---|---|
| **No delete** | DELETE endpoints are never called. Removing pages is always manual. |
| **Own pages only** | `deploy_page` verifies `page.creator._id == currentUser._id` before any write. |
| **Path containment** | Only files inside `GROWI_CONTENT_ROOT` can be read; path-traversal is rejected. |
| **Dry-run first** | Pass `dry_run=true` to preview what would happen without touching GROWI. |

## Requirements

- Python 3.11+ (3.12 recommended)
- [uv](https://docs.astral.sh/uv/)
- A running GROWI instance with a personal API token

## Installation

```bash
git clone https://github.com/toshiya-shimada/growi-mcp-server
cd growi-mcp-server
uv sync
```

## Configuration

Copy `.env.example` and fill in your values. The server reads environment variables directly (no `.env` file loading; pass them via your MCP host).

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROWI_BASE_URL` | ✓ | — | GROWI instance URL (no trailing slash) |
| `GROWI_ACCESS_TOKEN` | ✓ | — | Personal API token from `/me` in GROWI |
| `GROWI_CONTENT_ROOT` | ✓ for file tools | — | Root of your local Markdown git repo |
| `GROWI_ENABLE_WRITE_TOOLS` | | `false` | Set `true` to enable `deploy_page` |
| `GROWI_TIMEOUT_MS` | | `30000` | HTTP timeout in milliseconds |
| `GROWI_VERIFY_TLS` | | `true` | Verify GROWI TLS certificate |
| `MCP_TRANSPORT` | | `stdio` | `stdio` or `streamable-http` |
| `LOG_LEVEL` | | `INFO` | Python logging level |

## Markdown front-matter

Each article managed by this server must begin with a YAML front-matter block:

```markdown
---
growi_path: /dev/notes/api-design   # required: destination path in GROWI
grant: 1                             # optional: 1=public 2=restricted 4=specified 5=owner
tags: [api, design]                  # optional: page tags
---

# Article title

Body content starts here. The front-matter block is stripped before upload.
```

## Available tools

### Read (always enabled)

| Tool | Description |
|---|---|
| `whoami` | Return current authenticated user |
| `list_pages(path, limit, offset)` | List pages under a path prefix |
| `get_page(page_id?, path?)` | Get page details including body and creator |
| `search_pages(q, limit, offset, path?)` | Full-text search |
| `list_page_revisions(page_id, limit, offset)` | Revision history |
| `get_revision(revision_id)` | Single revision detail |
| `preview_frontmatter(file_path)` | Parse local md front-matter without writing |

### Write (requires `GROWI_ENABLE_WRITE_TOOLS=true`)

| Tool | Description |
|---|---|
| `deploy_page(file_path, dry_run?)` | Deploy local Markdown file to GROWI |

## Registering with Claude Code

```bash
claude mcp add growi \
  uv --directory /path/to/growi-mcp-server run growi-mcp-server \
  -e GROWI_BASE_URL=https://wiki.example.com \
  -e GROWI_ACCESS_TOKEN=your_token \
  -e GROWI_CONTENT_ROOT=/path/to/wiki \
  -e GROWI_ENABLE_WRITE_TOOLS=true
```

Or via `claude_desktop_config.json` — see [`examples/claude_desktop/config.json`](examples/claude_desktop/config.json).

## Typical workflow with Claude Code

```
User: edit articles/api-design.md and deploy it to GROWI

Claude: [edits the file locally]
Claude: [calls deploy_page(file_path="articles/api-design.md", dry_run=true)]
→ { action: "dry_run", would_action: "update", ownership_ok: true, target_path: "/dev/notes/api-design" }
Claude: [calls deploy_page(file_path="articles/api-design.md")]
→ { action: "updated", url: "https://wiki.example.com/dev/notes/api-design", ... }
```

## Development

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format .
uv run pyright
uv run pytest
```

## Architecture

Three-layer design (mirroring [redmine-mcp-server](https://github.com/toshiya-shimada/redmine-mcp-server)):

```
mcp_app/tools/      ← MCP presentation: tool registration & docstrings
domain/services.py  ← Business rules: ownership check, deploy orchestration
growi/endpoints/    ← HTTP adapter: thin wrappers around GROWI REST API v3
content/            ← Local file layer: path-safe loader + front-matter parser
```

## License

MIT
