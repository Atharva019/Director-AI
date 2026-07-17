"""
Unit tests for auth.firebase.initialize_firebase()'s configured-vs-not
credential handling. No real Firebase, no network.
"""

import pytest

import auth.firebase as firebase_module
from config import Settings, get_settings


@pytest.fixture(autouse=True)
def reset_firebase_app():
    """Ensure the module-level _firebase_app global doesn't leak across tests."""
    firebase_module._firebase_app = None
    yield
    firebase_module._firebase_app = None
    get_settings.cache_clear()


def test_configured_malformed_json_in_production_raises(monkeypatch):
    """Bad FIREBASE_SERVICE_ACCOUNT_JSON + is_production=True must fail fast."""
    settings = Settings(
        APP_ENV="production",
        FIREBASE_SERVICE_ACCOUNT_JSON="{not valid json",
        FIREBASE_CREDENTIALS_PATH="/nonexistent/path.json",
    )
    monkeypatch.setattr(firebase_module, "get_settings", lambda: settings)

    with pytest.raises(Exception):
        firebase_module.initialize_firebase()

    # Must not have silently fallen back to ADC.
    assert firebase_module._firebase_app is None


def test_not_configured_in_dev_falls_back_without_raising(monkeypatch):
    """No credential configured + not production -> quiet ADC/skip fallback."""
    settings = Settings(
        APP_ENV="development",
        FIREBASE_SERVICE_ACCOUNT_JSON="",
        FIREBASE_CREDENTIALS_PATH="/nonexistent/path.json",
    )
    monkeypatch.setattr(firebase_module, "get_settings", lambda: settings)

    class FakeApp:
        pass

    def fake_initialize_app(*args, **kwargs):
        if args or kwargs:
            # Called with a credential -> simulate failure (path doesn't exist).
            raise ValueError("no such file")
        # Called with no args -> simulate successful ADC init.
        return FakeApp()

    monkeypatch.setattr(firebase_module.firebase_admin, "initialize_app", fake_initialize_app)

    firebase_module.initialize_firebase()

    assert isinstance(firebase_module._firebase_app, FakeApp)
