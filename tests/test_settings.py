from africa_pulse.settings import Settings


def test_read_only_settings_do_not_require_a_tomtom_key(monkeypatch):
    monkeypatch.delenv("TOMTOM_API_KEY", raising=False)
    monkeypatch.setattr("africa_pulse.settings.load_local_env", lambda: None)

    assert Settings.from_environment().tomtom_api_key is None


def test_tomtom_key_is_required_only_when_tomtom_ingestion_starts(monkeypatch):
    monkeypatch.delenv("TOMTOM_API_KEY", raising=False)
    monkeypatch.setattr("africa_pulse.settings.load_local_env", lambda: None)

    try:
        Settings.from_environment().require_tomtom_api_key()
    except RuntimeError as error:
        assert "TOMTOM_API_KEY" in str(error)
    else:
        raise AssertionError("Expected a missing TomTom credential error")
