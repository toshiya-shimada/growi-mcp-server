from __future__ import annotations

import pydantic
import pytest

from growi_mcp_server.growi.errors import ConfigurationError
from growi_mcp_server.settings import Settings, load_settings


def test_valid_settings(tmp_path):
    s = Settings(
        growi_base_url="http://wiki.example.com",  # type: ignore[arg-type]
        growi_access_token="tok",
    )
    assert str(s.growi_base_url).startswith("http://wiki.example.com")
    assert s.growi_enable_write_tools is False


def test_missing_token_raises():
    with pytest.raises(pydantic.ValidationError):
        Settings(
            growi_base_url="http://wiki.example.com",  # type: ignore[arg-type]
            growi_access_token="",
        )


def test_content_root_must_exist(tmp_path):
    nonexistent = tmp_path / "does_not_exist"
    with pytest.raises(pydantic.ValidationError):
        Settings(
            growi_base_url="http://wiki.example.com",  # type: ignore[arg-type]
            growi_access_token="tok",
            growi_content_root=nonexistent,
        )


def test_content_root_existing_dir_ok(tmp_path):
    s = Settings(
        growi_base_url="http://wiki.example.com",  # type: ignore[arg-type]
        growi_access_token="tok",
        growi_content_root=tmp_path,
    )
    assert s.growi_content_root == tmp_path


def test_load_settings_raises_configuration_error(monkeypatch):
    monkeypatch.delenv("GROWI_BASE_URL", raising=False)
    monkeypatch.delenv("GROWI_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("GROWI_BASE_URL", "")
    # Clear lru_cache so the test gets a fresh call
    load_settings.cache_clear()
    with pytest.raises(ConfigurationError):
        load_settings()
    load_settings.cache_clear()
