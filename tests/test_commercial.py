from datetime import UTC, datetime
from types import SimpleNamespace

import httpx
import pytest

from africa_pulse.acquisition.commercial import OverpassCommercialClient
from africa_pulse.orchestration import context_collection


def test_overpass_retries_transient_status(monkeypatch):
    calls = []

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

    def post(_self, *_args, **_kwargs):
        calls.append(1)
        if len(calls) == 1:
            request = httpx.Request("POST", "https://example.test")
            response = httpx.Response(504, request=request)
            raise httpx.HTTPStatusError("timeout", request=request, response=response)
        return Response()

    monkeypatch.setattr(httpx.Client, "post", post)
    monkeypatch.setattr("africa_pulse.acquisition.commercial.time.sleep", lambda _seconds: None)

    assert OverpassCommercialClient(max_attempts=2)._post_with_retries("query").status_code == 200
    assert len(calls) == 2


def test_overpass_does_not_retry_non_transient_status(monkeypatch):
    request = httpx.Request("POST", "https://example.test")
    response = httpx.Response(400, request=request)

    def post(_self, *_args, **_kwargs):
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    monkeypatch.setattr(httpx.Client, "post", post)

    with pytest.raises(httpx.HTTPStatusError):
        OverpassCommercialClient(max_attempts=3)._post_with_retries("query")


def test_commercial_failure_before_all_cities_does_not_publish_partial_facts(monkeypatch):
    first_response = SimpleNamespace(
        payload={"elements": []},
        received_at=datetime(2026, 9, 14, tzinfo=UTC),
    )
    cities = (SimpleNamespace(city_id="lagos_ng"), SimpleNamespace(city_id="abuja_ng"))
    calls, inserted = [], []

    class Source:
        def fetch_snapshot(self, _city):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("source unavailable")
            return first_response

    monkeypatch.setattr(context_collection, "OverpassCommercialClient", Source)
    monkeypatch.setattr(context_collection, "persist_json_payload", lambda *_args: ("raw.json", "a" * 64))
    monkeypatch.setattr(context_collection, "insert_run_state", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(context_collection, "insert_rows", lambda _client, table, rows: inserted.append((table, rows)) or len(rows))

    with pytest.raises(RuntimeError, match="source unavailable"):
        context_collection.run_commercial(object(), cities)

    assert not any(table == "warehouse.fact_commercial_poi_snapshot" for table, _rows in inserted)
