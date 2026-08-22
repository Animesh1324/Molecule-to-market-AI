"""Security-relevant configuration guards.

Each test here pins a control that has no functional test elsewhere because
it only matters at startup, under a specific misconfiguration.
"""
import importlib
import os

import pytest


def _fresh_settings(monkeypatch, **env):
    """Reload app.config with a clean settings cache and the given env vars."""
    for key in ("CORS_ORIGINS",):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from app import config
    importlib.reload(config)
    config.get_settings.cache_clear()
    return config


def test_wildcard_cors_origin_is_rejected(monkeypatch):
    """allow_credentials=False now, but a wildcard origin is still refused
    outright rather than silently accepted — a future re-enable of
    credentials must not inherit a permissive value nobody meant to set.
    """
    config = _fresh_settings(monkeypatch, CORS_ORIGINS="*")
    with pytest.raises(RuntimeError, match="CORS_ORIGINS cannot"):
        config.get_settings()


def test_wildcard_among_multiple_origins_is_also_rejected(monkeypatch):
    config = _fresh_settings(monkeypatch, CORS_ORIGINS="https://real-site.example,*")
    with pytest.raises(RuntimeError, match="CORS_ORIGINS cannot"):
        config.get_settings()


def test_explicit_origins_are_accepted(monkeypatch):
    config = _fresh_settings(
        monkeypatch, CORS_ORIGINS="https://molecule-to-market-frontend.onrender.com")
    settings = config.get_settings()
    assert settings["cors_origins"] == ["https://molecule-to-market-frontend.onrender.com"]


def test_default_dev_origins_when_unset(monkeypatch):
    config = _fresh_settings(monkeypatch)
    settings = config.get_settings()
    assert "http://localhost:3000" in settings["cors_origins"]


def test_cors_middleware_does_not_allow_credentials():
    """No endpoint issues a cookie, so allow_credentials has no legitimate
    use — verified directly on the running app's middleware stack rather
    than just the config, since main.py could in principle hardcode True
    regardless of settings.
    """
    from app.main import app
    cors_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert cors_middleware.kwargs.get("allow_credentials") is False
