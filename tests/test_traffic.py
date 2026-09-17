from datetime import UTC, datetime

from africa_pulse.acquisition.tomtom import TrafficFlowResponse
from africa_pulse.orchestration.tomtom_collection import collection_slot, observation_key
from africa_pulse.transformation.traffic import congestion_ratio, validate_traffic_flow


def observation(**overrides):
    values = {
        "road_sample_id": "lagos_yaba",
        "observed_at": datetime(2026, 9, 12, tzinfo=UTC),
        "received_at": datetime(2026, 9, 12, tzinfo=UTC),
        "current_speed_kph": 20,
        "free_flow_speed_kph": 40,
        "current_travel_time_seconds": 120,
        "free_flow_travel_time_seconds": 60,
        "confidence": 0.9,
        "road_closure": False,
        "request_fingerprint": "a" * 64,
        "response_sha256": "b" * 64,
        "http_status": 200,
    }
    return TrafficFlowResponse(**(values | overrides))


def test_congestion_ratio_is_zero_at_free_flow():
    assert congestion_ratio(observation(current_speed_kph=40)) == 0.0


def test_congestion_ratio_represents_speed_reduction():
    assert congestion_ratio(observation()) == 0.5


def test_invalid_confidence_is_reported():
    outcomes = validate_traffic_flow(observation(confidence=1.1))
    assert any(result.rule_id == "traffic.confidence_in_range" and result.outcome == "fail" for result in outcomes)


def test_collection_slot_and_observation_key_make_reruns_idempotent():
    first = collection_slot(datetime(2026, 9, 12, 15, 58, tzinfo=UTC))
    second = collection_slot(datetime(2026, 9, 12, 15, 2, tzinfo=UTC))
    assert first == second == datetime(2026, 9, 12, 14, tzinfo=UTC)
    assert observation_key("lagos_ng", observation(), first) == observation_key("lagos_ng", observation(), second)
