from __future__ import annotations

from pathlib import Path

from growi_mcp_server.growi.errors import GrowiValidationError


def load_markdown_file(file_path: str, content_root: Path) -> str:
    """Read a Markdown file safely, ensuring it is within ``content_root``.

    Prevents path-traversal attacks (including symlink-based escapes) by
    resolving both paths to absolute form and verifying containment.

    Args:
        file_path: Path to the Markdown file (absolute or relative to cwd).
        content_root: The allowed root directory (``GROWI_CONTENT_ROOT``).

    Returns:
        The raw file contents as a UTF-8 string.

    Raises:
        GrowiValidationError: If the path is outside ``content_root``, the file
            does not exist, or the path is not a regular file.
    """
    resolved = Path(file_path).resolve()
    root_resolved = content_root.resolve()

    # Guard: path traversal
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise GrowiValidationError(
            f"File '{file_path}' is outside GROWI_CONTENT_ROOT '{root_resolved}'. "
            "Only files within the configured content root may be deployed."
        ) from exc

    if not resolved.exists():
        raise GrowiValidationError(f"File not found: '{resolved}'")

    if not resolved.is_file():
        raise GrowiValidationError(f"Path is not a regular file: '{resolved}'")

    return resolved.read_text(encoding="utf-8")
