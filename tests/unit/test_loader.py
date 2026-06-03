from __future__ import annotations

import pytest

from growi_mcp_server.content.loader import load_markdown_file
from growi_mcp_server.growi.errors import GrowiValidationError


def test_read_file_within_root(tmp_path):
    md = tmp_path / "article.md"
    md.write_text("Hello World", encoding="utf-8")
    result = load_markdown_file(str(md), tmp_path)
    assert result == "Hello World"


def test_path_traversal_blocked(tmp_path):
    outside = tmp_path.parent / "secret.txt"
    outside.write_text("SECRET", encoding="utf-8")
    with pytest.raises(GrowiValidationError, match="outside"):
        load_markdown_file(str(outside), tmp_path)


def test_dotdot_traversal_blocked(tmp_path):
    evil_path = str(tmp_path / ".." / "secret.txt")
    with pytest.raises(GrowiValidationError, match="outside"):
        load_markdown_file(evil_path, tmp_path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(GrowiValidationError, match="not found"):
        load_markdown_file(str(tmp_path / "nonexistent.md"), tmp_path)


def test_directory_path_raises(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    with pytest.raises(GrowiValidationError, match="not a regular file"):
        load_markdown_file(str(subdir), tmp_path)


def test_nested_file_allowed(tmp_path):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    md = sub / "page.md"
    md.write_text("Nested", encoding="utf-8")
    result = load_markdown_file(str(md), tmp_path)
    assert result == "Nested"
