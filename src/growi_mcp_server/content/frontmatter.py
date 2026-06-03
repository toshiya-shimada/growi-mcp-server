from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from growi_mcp_server.growi.errors import GrowiValidationError

_FENCE = "---"


@dataclass
class PageMeta:
    """Metadata extracted from YAML front-matter."""

    growi_path: str
    grant: int | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class ParsedMarkdown:
    """Result of parsing a Markdown file with YAML front-matter."""

    meta: PageMeta
    body: str  # raw Markdown body without the front-matter block


def parse_frontmatter(content: str) -> ParsedMarkdown:
    """Parse YAML front-matter from Markdown content.

    The file must begin with ``---``, contain valid YAML, and end the block
    with another ``---`` on its own line.  The ``growi_path`` key is required
    and must start with ``/``.

    Args:
        content: Full Markdown file contents.

    Returns:
        A :class:`ParsedMarkdown` with parsed meta and stripped body.

    Raises:
        GrowiValidationError: If front-matter is missing, malformed, or
            ``growi_path`` is absent or invalid.
    """
    if not content.startswith(_FENCE):
        raise GrowiValidationError(
            "Markdown file must begin with a YAML front-matter block (--- ... ---). "
            "Add 'growi_path: /your/page/path' to the front-matter."
        )

    # Find the closing fence (must be on its own line after the opening)
    rest = content[len(_FENCE) :]
    closing = rest.find(f"\n{_FENCE}")
    if closing == -1:
        raise GrowiValidationError(
            "YAML front-matter is not properly terminated. "
            "Ensure the block ends with '---' on its own line."
        )

    yaml_src = rest[:closing]
    body_raw = rest[closing + len(f"\n{_FENCE}") :]

    try:
        meta_raw: dict[str, object] = yaml.safe_load(yaml_src) or {}
    except yaml.YAMLError as exc:
        raise GrowiValidationError(f"Invalid YAML in front-matter: {exc}") from exc

    if not isinstance(meta_raw, dict):
        raise GrowiValidationError("Front-matter must be a YAML mapping.")

    growi_path = meta_raw.get("growi_path")
    if not growi_path:
        raise GrowiValidationError(
            "Front-matter must contain 'growi_path'. Example: growi_path: /your/page/path"
        )
    if not isinstance(growi_path, str):
        raise GrowiValidationError("'growi_path' must be a string.")
    if not growi_path.startswith("/"):
        raise GrowiValidationError(f"'growi_path' must start with '/'. Got: '{growi_path}'")

    grant_raw = meta_raw.get("grant")
    grant: int | None = None
    if grant_raw is not None:
        if not isinstance(grant_raw, int):
            raise GrowiValidationError(
                f"'grant' must be an integer (1=public, 2=restricted, 4=specified, 5=owner). "
                f"Got: {grant_raw!r}"
            )
        grant = grant_raw

    tags_raw = meta_raw.get("tags", [])
    if not isinstance(tags_raw, list):
        raise GrowiValidationError("'tags' must be a YAML list.")
    tags = [str(t) for t in tags_raw]

    return ParsedMarkdown(
        meta=PageMeta(growi_path=growi_path, grant=grant, tags=tags),
        body=body_raw.lstrip("\n"),
    )
