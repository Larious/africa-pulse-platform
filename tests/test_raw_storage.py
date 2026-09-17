from datetime import UTC, datetime
from pathlib import Path

from africa_pulse.storage import raw


def test_persist_json_payload_is_deterministic_and_immutable(tmp_path, monkeypatch):
    monkeypatch.setattr(raw, "PROJECT_ROOT", tmp_path)
    received_at = datetime(2026, 9, 12, 15, 0, tzinfo=UTC)
    first_path, first_hash = raw.persist_json_payload("weather", {"b": 2, "a": 1}, received_at)
    second_path, second_hash = raw.persist_json_payload("weather", {"a": 1, "b": 2}, received_at)
    assert first_path == second_path
    assert first_hash == second_hash
    assert Path(tmp_path / first_path).exists()
