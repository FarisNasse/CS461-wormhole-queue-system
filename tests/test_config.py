import importlib


def _reload_config(monkeypatch, app_env=None, **overrides):
    names = {
        "APP_ENV",
        "FORCE_HTTPS",
        "ENABLE_HSTS",
        "SESSION_COOKIE_SECURE",
        "PREFERRED_URL_SCHEME",
    }

    for name in names:
        monkeypatch.delenv(name, raising=False)

    if app_env is not None:
        monkeypatch.setenv("APP_ENV", app_env)

    for name, value in overrides.items():
        monkeypatch.setenv(name, value)

    import config

    return importlib.reload(config)


def test_config_defaults_to_secure_production_settings(monkeypatch):
    config = _reload_config(monkeypatch)

    assert config.Config.APP_ENV == "production"
    assert config.Config.FORCE_HTTPS is True
    assert config.Config.ENABLE_HSTS is True
    assert config.Config.SESSION_COOKIE_SECURE is True
    assert config.Config.PREFERRED_URL_SCHEME == "https"


def test_config_uses_http_defaults_for_development(monkeypatch):
    config = _reload_config(monkeypatch, app_env="development")

    assert config.Config.APP_ENV == "development"
    assert config.Config.FORCE_HTTPS is False
    assert config.Config.ENABLE_HSTS is False
    assert config.Config.SESSION_COOKIE_SECURE is False
    assert config.Config.PREFERRED_URL_SCHEME == "http"


def test_config_allows_explicit_security_overrides(monkeypatch):
    config = _reload_config(
        monkeypatch,
        app_env="development",
        FORCE_HTTPS="1",
        ENABLE_HSTS="1",
        SESSION_COOKIE_SECURE="1",
        PREFERRED_URL_SCHEME="https",
    )

    assert config.Config.FORCE_HTTPS is True
    assert config.Config.ENABLE_HSTS is True
    assert config.Config.SESSION_COOKIE_SECURE is True
    assert config.Config.PREFERRED_URL_SCHEME == "https"
