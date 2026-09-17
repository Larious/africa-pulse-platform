import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from africa_pulse.acquisition.exchange_rates import SOURCE_ID as FX_SOURCE_ID
from africa_pulse.acquisition.exchange_rates import ExchangeRateClient
from africa_pulse.acquisition.open_meteo import (
    AIR_QUALITY_SOURCE_ID,
    WEATHER_SOURCE_ID,
    OpenMeteoClient,
)
from africa_pulse.config import load_cities
from africa_pulse.orchestration.tomtom_collection import (
    collection_slot,
    insert_run_state,
    seed_reference_data,
)
from africa_pulse.settings import Settings
from africa_pulse.storage.raw import persist_json_payload
from africa_pulse.warehouse.client import get_client, insert_rows

RAW_RETENTION_POLICY = "local_ignored_raw_payload_storage"


def make_observation_key(source_id: str, entity_id: str, observed_at: datetime) -> str:
    identity = {
        "source_id": source_id,
        "entity_id": entity_id,
        "collection_slot": collection_slot(observed_at).isoformat(),
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def row_exists(client, table: str, key: str) -> bool:
    query = f"SELECT count() FROM {table} WHERE observation_key = {{key:String}}"
    return client.query(query, parameters={"key": key}).result_rows[0][0] > 0


def write_evidence(client, run_id, source_id, city_id, response, payload_uri, response_sha256):
    evidence_id = uuid4()
    insert_rows(client, "control.raw_evidence", [{
        "evidence_id": evidence_id, "run_id": run_id, "source_id": source_id, "city_id": city_id,
        "request_fingerprint": response.request_fingerprint, "response_sha256": response_sha256,
        "received_at": response.received_at, "payload_uri": payload_uri,
        "retention_policy": RAW_RETENTION_POLICY, "http_status": 200,
    }])
    return evidence_id


def write_quality_result(client, run_id, source_id, city_id, rule_id, passed, observed_at, evidence_id, reason=None):
    insert_rows(client, "quality.rule_result", [{
        "result_id": uuid4(), "run_id": run_id, "source_id": source_id, "city_id": city_id,
        "rule_id": rule_id, "severity": "error", "outcome": "pass" if passed else "fail",
        "observed_at": observed_at, "numerator": 1 if passed else 0, "denominator": 1,
        "reason": reason, "evidence_id": evidence_id,
    }])


def run_weather(client, cities) -> dict[str, int | str]:
    run_id, started_at = uuid4(), datetime.now(UTC)
    insert_run_state(client, run_id, WEATHER_SOURCE_ID, "running", started_at)
    received = inserted = quarantined = 0
    try:
        source = OpenMeteoClient()
        for city in cities:
            response = source.fetch_weather(city)
            received += 1
            payload_uri, response_sha256 = persist_json_payload(WEATHER_SOURCE_ID, response.payload, response.received_at)
            evidence_id = write_evidence(client, run_id, WEATHER_SOURCE_ID, city.city_id, response, payload_uri, response_sha256)
            valid = -80 <= response.temperature_celsius <= 65 and response.precipitation_mm >= 0 and response.wind_speed_kph >= 0
            write_quality_result(client, run_id, WEATHER_SOURCE_ID, city.city_id, "weather.physical_ranges", valid, response.observed_at, evidence_id, None if valid else "weather values outside physical range")
            if not valid:
                quarantined += 1
                continue
            key = make_observation_key(WEATHER_SOURCE_ID, city.city_id, response.observed_at)
            if row_exists(client, "warehouse.fact_weather_observation", key):
                continue
            inserted += insert_rows(client, "warehouse.fact_weather_observation", [{
                "observation_key": key, "source_id": WEATHER_SOURCE_ID, "run_id": run_id, "city_id": city.city_id,
                "observed_at": response.observed_at, "received_at": response.received_at,
                "temperature_celsius": response.temperature_celsius, "precipitation_mm": response.precipitation_mm,
                "wind_speed_kph": response.wind_speed_kph, "response_sha256": response_sha256, "ingested_at": datetime.now(UTC),
            }])
    except Exception as error:
        insert_run_state(client, run_id, WEATHER_SOURCE_ID, "failed", started_at, received, inserted, quarantined, str(error))
        raise
    insert_run_state(client, run_id, WEATHER_SOURCE_ID, "completed", started_at, received, inserted, quarantined)
    return {"source_id": WEATHER_SOURCE_ID, "records_received": received, "records_inserted": inserted, "records_quarantined": quarantined}


def run_air_quality(client, cities) -> dict[str, int | str]:
    run_id, started_at = uuid4(), datetime.now(UTC)
    insert_run_state(client, run_id, AIR_QUALITY_SOURCE_ID, "running", started_at)
    received = inserted = quarantined = 0
    try:
        source = OpenMeteoClient()
        for city in cities:
            response = source.fetch_air_quality(city)
            received += 1
            payload_uri, response_sha256 = persist_json_payload(AIR_QUALITY_SOURCE_ID, response.payload, response.received_at)
            evidence_id = write_evidence(client, run_id, AIR_QUALITY_SOURCE_ID, city.city_id, response, payload_uri, response_sha256)
            valid = response.pm2_5 >= 0 and response.pm10 >= 0 and response.nitrogen_dioxide >= 0
            write_quality_result(client, run_id, AIR_QUALITY_SOURCE_ID, city.city_id, "air_quality.non_negative", valid, response.observed_at, evidence_id, None if valid else "negative concentration")
            if not valid:
                quarantined += 1
                continue
            key = make_observation_key(AIR_QUALITY_SOURCE_ID, city.city_id, response.observed_at)
            if row_exists(client, "warehouse.fact_air_quality_observation", key):
                continue
            inserted += insert_rows(client, "warehouse.fact_air_quality_observation", [{
                "observation_key": key, "source_id": AIR_QUALITY_SOURCE_ID, "run_id": run_id, "city_id": city.city_id,
                "observed_at": response.observed_at, "received_at": response.received_at,
                "pm2_5_micrograms_per_cubic_metre": response.pm2_5, "pm10_micrograms_per_cubic_metre": response.pm10,
                "nitrogen_dioxide_micrograms_per_cubic_metre": response.nitrogen_dioxide,
                "response_sha256": response_sha256, "ingested_at": datetime.now(UTC),
            }])
    except Exception as error:
        insert_run_state(client, run_id, AIR_QUALITY_SOURCE_ID, "failed", started_at, received, inserted, quarantined, str(error))
        raise
    insert_run_state(client, run_id, AIR_QUALITY_SOURCE_ID, "completed", started_at, received, inserted, quarantined)
    return {"source_id": AIR_QUALITY_SOURCE_ID, "records_received": received, "records_inserted": inserted, "records_quarantined": quarantined}


def run_fx(client, cities) -> dict[str, int | str]:
    run_id, started_at = uuid4(), datetime.now(UTC)
    insert_run_state(client, run_id, FX_SOURCE_ID, "running", started_at)
    received = inserted = quarantined = 0
    try:
        response = ExchangeRateClient().fetch_usd_rates({city.currency_code for city in cities})
        payload_uri, response_sha256 = persist_json_payload(FX_SOURCE_ID, response.payload, response.received_at)
        for currency, rate in response.rates.items():
            received += 1
            evidence_id = write_evidence(client, run_id, FX_SOURCE_ID, currency, response, payload_uri, response_sha256)
            valid = rate > 0
            write_quality_result(client, run_id, FX_SOURCE_ID, currency, "fx.rate_positive", valid, response.observed_at, evidence_id, None if valid else "rate <= 0")
            if not valid:
                quarantined += 1
                continue
            key = make_observation_key(FX_SOURCE_ID, currency, response.observed_at)
            if row_exists(client, "warehouse.fact_fx_rate", key):
                continue
            inserted += insert_rows(client, "warehouse.fact_fx_rate", [{
                "observation_key": key, "source_id": FX_SOURCE_ID, "run_id": run_id, "base_currency": "USD",
                "quote_currency": currency, "observed_at": response.observed_at, "received_at": response.received_at,
                "rate_quote_per_base": rate, "response_sha256": response_sha256, "ingested_at": datetime.now(UTC),
            }])
    except Exception as error:
        insert_run_state(client, run_id, FX_SOURCE_ID, "failed", started_at, received, inserted, quarantined, str(error))
        raise
    insert_run_state(client, run_id, FX_SOURCE_ID, "completed", started_at, received, inserted, quarantined)
    return {"source_id": FX_SOURCE_ID, "records_received": received, "records_inserted": inserted, "records_quarantined": quarantined}


def run() -> list[dict[str, int | str]]:
    client = get_client(Settings.from_environment())
    cities = load_cities()
    seed_reference_data(client, cities)
    return [run_weather(client, cities), run_air_quality(client, cities), run_fx(client, cities)]


if __name__ == "__main__":
    print(run())
