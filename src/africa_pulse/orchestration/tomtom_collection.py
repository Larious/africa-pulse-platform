import hashlib
import json
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from africa_pulse.acquisition.tomtom import SOURCE_ID, TomTomTrafficClient, TrafficFlowResponse
from africa_pulse.config import City, load_cities
from africa_pulse.settings import Settings
from africa_pulse.transformation.traffic import validate_traffic_flow
from africa_pulse.warehouse.client import get_client, insert_rows

CODE_VERSION = "initial-tomtom-vertical-slice"
RETENTION_POLICY = "metadata_and_normalised_measures_only_pending_terms_review"


def safe_error_message(error: Exception) -> str:
    """Keep credentials and signed query parameters out of operational evidence."""
    message = str(error)
    message = re.sub(r"([?&]key=)[^&'\\\" ]+", r"\1REDACTED", message, flags=re.IGNORECASE)
    message = re.sub(r"(https?://[^ ]*?)([?&]key=)[^&'\\\" ]+", r"\1\2REDACTED", message, flags=re.IGNORECASE)
    return message[:1000]


def collection_slot(timestamp: datetime) -> datetime:
    """Round a timestamp down to the configured two-hour collection slot."""
    utc_timestamp = timestamp.astimezone(UTC)
    return utc_timestamp.replace(hour=utc_timestamp.hour - utc_timestamp.hour % 2, minute=0, second=0, microsecond=0)


def observation_key(city_id: str, response: TrafficFlowResponse, slot: datetime) -> str:
    """A rerun of the same city, road sample, and scheduled slot gets the same key."""
    identity = {
        "source_id": SOURCE_ID,
        "city_id": city_id,
        "road_sample_id": response.road_sample_id,
        "collection_slot": slot.isoformat(),
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def seed_reference_data(client, cities: tuple[City, ...]) -> None:
    today = datetime.now(UTC).date()
    city_rows = []
    road_rows = []
    for city in cities:
        city_rows.append(
            {
                "city_id": city.city_id,
                "city_name": city.city_name,
                "country_code": city.country_code,
                "country_name": city.country_name,
                "timezone": city.timezone,
                "currency_code": city.currency_code,
                "valid_from": today,
                "valid_to": None,
                "boundary_version": "initial_reference_point_samples_v1",
            }
        )
        for road in city.road_samples:
            road_rows.append(
                {
                    "road_sample_id": road.road_sample_id,
                    "city_id": city.city_id,
                    "label": road.label,
                    "latitude": road.latitude,
                    "longitude": road.longitude,
                    "selection_rule": "validated_distributed_road_adjacent_reference_point_v1",
                    "valid_from": today,
                    "valid_to": None,
                }
            )
    insert_rows(client, "warehouse.dim_city", city_rows)
    insert_rows(client, "warehouse.dim_road_sample", road_rows)
    insert_rows(
        client,
        "warehouse.dim_source",
        [
            {
                "source_id": SOURCE_ID,
                "source_name": "TomTom Traffic Flow API",
                "domain": "mobility",
                "refresh_cadence": "every 2 hours",
                "observation_grain": "one provider response for one configured road sample in one collection slot",
                "retention_policy": RETENTION_POLICY,
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
            {
                "source_id": "open_meteo_weather_v1",
                "source_name": "Open-Meteo Forecast API",
                "domain": "climate",
                "refresh_cadence": "every 2 hours",
                "observation_grain": "one weather snapshot at one configured city reference coordinate",
                "retention_policy": "local_ignored_raw_payload_storage",
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
            {
                "source_id": "open_meteo_air_quality_v1",
                "source_name": "Open-Meteo Air Quality API",
                "domain": "environment",
                "refresh_cadence": "every 2 hours",
                "observation_grain": "one modelled air-quality snapshot at one configured city reference coordinate",
                "retention_policy": "local_ignored_raw_payload_storage",
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
            {
                "source_id": "exchange_rate_api_usd_v6",
                "source_name": "ExchangeRate-API USD endpoint",
                "domain": "market",
                "refresh_cadence": "every 2 hours",
                "observation_grain": "one USD-to-currency rate snapshot per target currency",
                "retention_policy": "local_ignored_raw_payload_storage",
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
            {
                "source_id": "openstreetmap_overpass_commercial_v1",
                "source_name": "OpenStreetMap via Overpass API",
                "domain": "commercial_geospatial",
                "refresh_cadence": "weekly",
                "observation_grain": "one commercial category count for one city candidate area and snapshot time",
                "retention_policy": "local_ignored_raw_payload_storage",
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
            {
                "source_id": "world_bank_indicators_v2",
                "source_name": "World Bank Indicators API",
                "domain": "economic_context",
                "refresh_cadence": "monthly",
                "observation_grain": "one country indicator, reference year, and published source value",
                "retention_policy": "local_ignored_raw_payload_storage",
                "attribution_required": True,
                "contract_version": "v1",
                "valid_from": today,
            },
        ],
    )


def run() -> dict[str, int | str]:
    settings = Settings.from_environment()
    client = get_client(settings)
    cities = load_cities()
    seed_reference_data(client, cities)

    run_id = uuid4()
    started_at = datetime.now(UTC)
    insert_run_state(client, run_id, SOURCE_ID, "running", started_at)
    source_client = TomTomTrafficClient(settings.require_tomtom_api_key())
    received = inserted = quarantined = 0
    source_errors: list[str] = []

    try:
        for city in cities:
            for road_sample in city.road_samples:
                try:
                    response = source_client.fetch_flow(road_sample)
                except Exception as error:  # noqa: BLE001 - isolate one unavailable sample.
                    source_errors.append(
                        f"{city.city_id}/{road_sample.road_sample_id}: {safe_error_message(error)}"
                    )
                    continue
                received += 1
                evidence_id = uuid4()
                insert_rows(
                    client,
                    "control.raw_evidence",
                    [
                        {
                            "evidence_id": evidence_id,
                            "run_id": run_id,
                            "source_id": SOURCE_ID,
                            "city_id": city.city_id,
                            "request_fingerprint": response.request_fingerprint,
                            "response_sha256": response.response_sha256,
                            "received_at": response.received_at,
                            "payload_uri": None,
                            "retention_policy": RETENTION_POLICY,
                            "http_status": response.http_status,
                        }
                    ],
                )
                validation_results = validate_traffic_flow(response)
                is_valid = all(result.outcome == "pass" for result in validation_results)
                insert_quality_results(client, run_id, city.city_id, evidence_id, response, validation_results)
                if not is_valid:
                    quarantined += 1
                    continue

                slot = collection_slot(response.observed_at)
                key = observation_key(city.city_id, response, slot)
                if fact_exists(client, key):
                    continue
                inserted += insert_rows(
                    client,
                    "warehouse.fact_traffic_flow_observation",
                    [
                        {
                            "observation_key": key,
                            "source_id": SOURCE_ID,
                            "run_id": run_id,
                            "city_id": city.city_id,
                            "road_sample_id": response.road_sample_id,
                            "collection_slot": slot,
                            "observed_at": response.observed_at,
                            "received_at": response.received_at,
                            "current_speed_kph": response.current_speed_kph,
                            "free_flow_speed_kph": response.free_flow_speed_kph,
                            "current_travel_time_seconds": response.current_travel_time_seconds,
                            "free_flow_travel_time_seconds": response.free_flow_travel_time_seconds,
                            "confidence": response.confidence,
                            "road_closure": response.road_closure,
                            "response_sha256": response.response_sha256,
                            "ingested_at": datetime.now(UTC),
                        }
                    ],
                )
    except Exception as error:
        insert_run_state(
            client, run_id, SOURCE_ID, "failed", started_at, received, inserted, quarantined, safe_error_message(error)
        )
        raise

    status = "partial" if source_errors else "completed"
    insert_run_state(
        client,
        run_id,
        SOURCE_ID,
        status,
        started_at,
        received,
        inserted,
        quarantined,
        "; ".join(source_errors) if source_errors else None,
    )
    return {
        "run_id": str(run_id),
        "records_received": received,
        "records_inserted": inserted,
        "records_quarantined": quarantined,
        "records_failed": len(source_errors),
    }


def fact_exists(client, key: str) -> bool:
    query = "SELECT count() FROM warehouse.fact_traffic_flow_observation WHERE observation_key = {key:String}"
    result = client.query(query, parameters={"key": key})
    return result.result_rows[0][0] > 0


def insert_run_state(
    client,
    run_id: UUID,
    source_id: str,
    status: str,
    started_at: datetime,
    received: int = 0,
    inserted: int = 0,
    quarantined: int = 0,
    error_message: str | None = None,
) -> None:
    completed_at = datetime.now(UTC) if status in {"completed", "partial", "failed"} else None
    insert_rows(
        client,
        "control.ingestion_run",
        [
            {
                "run_id": run_id,
                "source_id": source_id,
                "status": status,
                "started_at": started_at,
                "completed_at": completed_at,
                "records_received": received,
                "records_inserted": inserted,
                "records_quarantined": quarantined,
                "error_message": error_message,
                "code_version": CODE_VERSION,
                "updated_at": datetime.now(UTC),
            }
        ],
    )


def insert_quality_results(client, run_id, city_id, evidence_id, response, validation_results) -> None:
    rows = []
    for result in validation_results:
        rows.append(
            {
                "result_id": uuid4(),
                "run_id": run_id,
                "source_id": SOURCE_ID,
                "city_id": city_id,
                "rule_id": result.rule_id,
                "severity": "error",
                "outcome": result.outcome,
                "observed_at": response.observed_at,
                "numerator": 1 if result.outcome == "pass" else 0,
                "denominator": 1,
                "reason": result.reason,
                "evidence_id": evidence_id,
            }
        )
    insert_rows(client, "quality.rule_result", rows)


if __name__ == "__main__":
    print(run())
