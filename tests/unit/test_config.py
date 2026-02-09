import pytest

import myapp.config as config


def test_get_config_known_names():
    assert config.get_config("development").__name__ == "DevelopmentConfig"
    assert config.get_config("dev").__name__ == "DevelopmentConfig"
    assert config.get_config("testing").__name__ == "TestingConfig"
    assert config.get_config("prod").__name__ == "ProductionConfig"


def test_get_config_unknown_raises_value_error():
    with pytest.raises(ValueError) as exc:
        config.get_config("nope")
    assert "Unknown CONFIG=" in str(exc.value)


def test_baseconfig_secret_key_default_used_when_env_missing(monkeypatch):
    # Ensure SECRET_KEY env var is missing
    monkeypatch.delenv("SECRET_KEY", raising=False)

    # Re-create a config class instance so defaults are evaluated
    # (dataclass defaults are evaluated at import-time, so we need to call the attribute directly)
    secret = config.BaseConfig().SECRET_KEY
    assert isinstance(secret, str)
    assert len(secret) > 0


def test_env_bool_parsing(monkeypatch):
    monkeypatch.setenv("SQLALCHEMY_ECHO", "1")
    assert config._env_bool("SQLALCHEMY_ECHO") is True

    monkeypatch.setenv("SQLALCHEMY_ECHO", "false")
    assert config._env_bool("SQLALCHEMY_ECHO") is False
