from datetime import UTC, datetime

from africa_pulse.orchestration import refresh_marts


class QueryClient:
    def __init__(self, responses):
        self.responses = responses

    def query(self, query):
        for marker, response in self.responses.items():
            if marker in query:
                return NamedResults(response)
        raise AssertionError(f"Unexpected query: {query}")


class NamedResults:
    def __init__(self, values):
        self.values = values

    def named_results(self):
        return self.values


def test_local_date_uses_each_city_timezone():
    timestamp = datetime(2026, 9, 12, 23, 30, tzinfo=UTC)
    assert refresh_marts.local_date(timestamp, "Africa/Lagos").isoformat() == "2026-09-13"
    assert refresh_marts.local_date(timestamp, "Africa/Johannesburg").isoformat() == "2026-09-13"


def test_mobility_daily_uses_distinct_road_samples_for_coverage(monkeypatch):
    client = QueryClient({
        "fact_traffic_flow_observation": [
            {"city_id": "lagos_ng", "road_sample_id": "a", "observed_at": datetime(2026, 9, 12, 8, tzinfo=UTC), "current_speed_kph": 20, "free_flow_speed_kph": 40, "confidence": 0.9},
            {"city_id": "lagos_ng", "road_sample_id": "a", "observed_at": datetime(2026, 9, 12, 10, tzinfo=UTC), "current_speed_kph": 30, "free_flow_speed_kph": 40, "confidence": 0.8},
            {"city_id": "lagos_ng", "road_sample_id": "b", "observed_at": datetime(2026, 9, 12, 10, tzinfo=UTC), "current_speed_kph": 40, "free_flow_speed_kph": 40, "confidence": 0.7},
        ],
        "dim_road_sample": [{"city_id": "lagos_ng", "count": 5}],
    })
    inserted = []
    monkeypatch.setattr(refresh_marts, "insert_rows", lambda _client, _table, records: inserted.extend(records))

    refresh_marts.refresh_mobility(
        client,
        {"lagos_ng": {"timezone": "Africa/Lagos"}},
        datetime(2026, 9, 12, tzinfo=UTC),
    )

    assert inserted[0]["observations"] == 3
    assert inserted[0]["valid_sample_coverage_pct"] == 40


def test_economic_daily_uses_latest_grouped_results(monkeypatch):
    client = QueryClient({
        "GROUP BY quote_currency": [{"quote_currency": "NGN", "latest_observed_at": datetime(2026, 9, 12, tzinfo=UTC), "rate_quote_per_base": 1500.0}],
        "GROUP BY country_code": [{"country_code": "NGA", "latest_value": 21.4, "latest_reference_year": 2025}],
    })
    inserted = []
    monkeypatch.setattr(refresh_marts, "insert_rows", lambda _client, _table, records: inserted.extend(records))

    refresh_marts.refresh_economic(
        client,
        {"lagos_ng": {"timezone": "Africa/Lagos", "currency_code": "NGN", "country_code": "NGA"}},
        datetime(2026, 9, 12, tzinfo=UTC),
    )

    assert inserted[0]["latest_country_inflation_year"] == 2025
    assert inserted[0]["latest_country_inflation_pct"] == 21.4


def test_intelligence_score_remains_unavailable_with_partial_coverage(monkeypatch):
    client = QueryClient({
        "city_mobility_daily": [{"city_id": "lagos_ng", "local_date": datetime(2026, 9, 12, tzinfo=UTC).date(), "median_congestion_ratio": 0.2}],
        "city_climate_environment_daily": [{"city_id": "lagos_ng", "local_date": datetime(2026, 9, 12, tzinfo=UTC).date(), "average_pm2_5_micrograms_per_cubic_metre": 12}],
    })
    inserted = []
    monkeypatch.setattr(refresh_marts, "insert_rows", lambda _client, _table, records: inserted.extend(records))

    refresh_marts.refresh_intelligence(client, {}, datetime(2026, 9, 12, tzinfo=UTC))

    assert inserted[0]["weighted_coverage_pct"] == 50
    assert inserted[0]["score_status"] == "unavailable"
    assert inserted[0]["city_intelligence_score"] is None
