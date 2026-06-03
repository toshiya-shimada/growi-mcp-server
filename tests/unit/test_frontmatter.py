from __future__ import annotations

import pytest

from growi_mcp_server.content.frontmatter import parse_frontmatter
from growi_mcp_server.growi.errors import GrowiValidationError


def test_basic_parse():
    content = "---\ngrowi_path: /foo/bar\n---\n# Hello\nWorld"
    parsed = parse_frontmatter(content)
    assert parsed.meta.growi_path == "/foo/bar"
    assert parsed.meta.grant is None
    assert parsed.meta.tags == []
    assert parsed.body.startswith("# Hello")


def test_parse_with_grant_and_tags():
    content = "---\ngrowi_path: /docs/api\ngrant: 2\ntags:\n  - api\n  - backend\n---\nBody"
    parsed = parse_frontmatter(content)
    assert parsed.meta.grant == 2
    assert parsed.meta.tags == ["api", "backend"]
    assert parsed.body == "Body"


def test_frontmatter_stripped_from_body():
    content = "---\ngrowi_path: /p\n---\n\nActual content here."
    parsed = parse_frontmatter(content)
    assert "growi_path" not in parsed.body
    assert "---" not in parsed.body
    assert "Actual content here." in parsed.body


def test_missing_fence_raises():
    with pytest.raises(GrowiValidationError, match="front-matter"):
        parse_frontmatter("# No frontmatter here")


def test_unclosed_fence_raises():
    with pytest.raises(GrowiValidationError, match="terminated"):
        parse_frontmatter("---\ngrowi_path: /foo\nno closing fence")


def test_missing_growi_path_raises():
    with pytest.raises(GrowiValidationError, match="growi_path"):
        parse_frontmatter("---\ngrant: 1\n---\nBody")


def test_growi_path_must_start_with_slash():
    with pytest.raises(GrowiValidationError, match="'/'"):
        parse_frontmatter("---\ngrowi_path: no-slash\n---\nBody")


def test_invalid_yaml_raises():
    with pytest.raises(GrowiValidationError, match="YAML"):
        parse_frontmatter("---\n: invalid: yaml: [\n---\nBody")


def test_grant_must_be_int():
    with pytest.raises(GrowiValidationError, match="grant"):
        parse_frontmatter("---\ngrowi_path: /p\ngrant: public\n---\nBody")
