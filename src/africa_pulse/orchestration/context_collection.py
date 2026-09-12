from datetime import UTC, datetime
from uuid import uuid4

from africa_pulse.acquisition.commercial import SOURCE_ID as COMMERCIAL_SOURCE_ID
from africa_pulse.acquisition.commercial import OverpassCommercialClient
from africa_pulse.acquisition.world_bank import SOURCE_ID as ECONOMIC_SOURCE_ID
from africa_pulse.acquisition.world_bank import WorldBankClient
from africa_pulse.config import load_cities
from africa_pulse.orchestration.public_collection import (
    make_observation_key,
    row_exists,
    write_evidence,
    write_quality_result,
)
from africa_pulse.orchestration.tomtom_collection import insert_run_state, seed_reference_data
from africa_pulse.settings import Settings
from africa_pulse.storage.raw import persist_json_payload
from africa_pulse.warehouse.client import get_client, insert_rows


def run_commercial(client, cities):
    run_id, started_at = uuid4(), datetime.now(UTC)
    insert_run_state(client, run_id, COMMERCIAL_SOURCE_ID, "running", started_at)
    received = inserted = 0
    try:
        for city in cities:
            response = OverpassCommercialClient().fetch_snapshot(city)
            payload_uri, checksum = persist_json_payload(COMMERCIAL_SOURCE_ID, response.payload, response.received_at)
            evidence_id = write_evidence(client, run_id, COMMERCIAL_SOURCE_ID, city.city_id, response, payload_uri, checksum)
            for category, count in response.category_counts.items():
                received += 1
                valid = count >= 0
                write_quality_result(client, run_id, COMMERCIAL_SOURCE_ID, city.city_id, "commercial.count_non_negative", valid, response.snapshot_at, evidence_id)
                key = make_observation_key(COMMERCIAL_SOURCE_ID, f"{city.city_id}:{category}", response.snapshot_at)
                if valid and not row_exists(client, "warehouse.fact_commercial_poi_snapshot", key):
                    inserted += insert_rows(client, "warehouse.fact_commercial_poi_snapshot", [{
                        "observation_key": key, "source_id": COMMERCIAL_SOURCE_ID, "run_id": run_id, "city_id": city.city_id,
                        "snapshot_at": response.snapshot_at, "category": category, "poi_count": count,
                        "area_definition": "candidate_area_bbox_v1", "response_sha256": checksum, "ingested_at": datetime.now(UTC),
                    }])
    except Exception as error:
        insert_run_state(client, run_id, COMMERCIAL_SOURCE_ID, "failed", started_at, received, inserted, 0, str(error))
        raise
    insert_run_state(client, run_id, COMMERCIAL_SOURCE_ID, "completed", started_at, received, inserted, 0)
    return {"source_id": COMMERCIAL_SOURCE_ID, "records_received": received, "records_inserted": inserted}


def run_economic_context(client, cities):
    run_id, started_at = uuid4(), datetime.now(UTC)
    insert_run_state(client, run_id, ECONOMIC_SOURCE_ID, "running", started_at)
    received = inserted = 0
    try:
        response = WorldBankClient().fetch_indicators({city.country_code for city in cities})
        payload_uri, checksum = persist_json_payload(ECONOMIC_SOURCE_ID, response.payload, response.received_at)
        evidence_id = write_evidence(client, run_id, ECONOMIC_SOURCE_ID, "country_context", response, payload_uri, checksum)
        for release in response.releases:
            received += 1
            valid = release.value == release.value
            write_quality_result(client, run_id, ECONOMIC_SOURCE_ID, release.country_code, "economic.value_present", valid, response.received_at, evidence_id)
            key = make_observation_key(ECONOMIC_SOURCE_ID, f"{release.country_code}:{release.indicator_code}:{release.reference_year}", response.received_at)
            if valid and not row_exists(client, "warehouse.fact_economic_indicator_release", key):
                inserted += insert_rows(client, "warehouse.fact_economic_indicator_release", [{
                    "observation_key": key, "source_id": ECONOMIC_SOURCE_ID, "run_id": run_id,
                    "country_code": release.country_code, "indicator_code": release.indicator_code,
                    "indicator_name": release.indicator_name, "reference_year": release.reference_year,
                    "value": release.value, "received_at": response.received_at, "response_sha256": checksum,
                    "ingested_at": datetime.now(UTC),
                }])
    except Exception as error:
        insert_run_state(client, run_id, ECONOMIC_SOURCE_ID, "failed", started_at, received, inserted, 0, str(error))
        raise
    insert_run_state(client, run_id, ECONOMIC_SOURCE_ID, "completed", started_at, received, inserted, 0)
    return {"source_id": ECONOMIC_SOURCE_ID, "records_received": received, "records_inserted": inserted}


def run():
    client = get_client(Settings.from_environment())
    cities = load_cities()
    seed_reference_data(client, cities)
    return [run_commercial(client, cities), run_economic_context(client, cities)]


if __name__ == "__main__":
    print(run())
