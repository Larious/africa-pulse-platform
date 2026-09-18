import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from africa_pulse.config import RoadSample

SOURCE_ID = "tomtom_traffic_flow_v4"
FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


@dataclass(frozen=True)
class TrafficFlowResponse:
    road_sample_id: str
    observed_at: datetime
    received_at: datetime
    current_speed_kph: int
    free_flow_speed_kph: int
    current_travel_time_seconds: int
    free_flow_travel_time_seconds: int
    confidence: float
    road_closure: bool
    request_fingerprint: str
    response_sha256: str
    http_status: int


class TomTomTrafficClient:
    def __init__(self, api_key: str, timeout_seconds: float = 20.0) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def fetch_flow(self, road_sample: RoadSample) -> TrafficFlowResponse:
        received_at = datetime.now(UTC)
        public_request = {
            "point": f"{road_sample.latitude},{road_sample.longitude}",
            "unit": "KMPH",
        }
        request_fingerprint = hashlib.sha256(
            json.dumps(public_request, sort_keys=True).encode()
        ).hexdigest()
        params = {**public_request, "key": self._api_key}

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.get(FLOW_URL, params=params)
            if response.is_error:
                # Never propagate httpx's request URL because it includes the API key.
                raise RuntimeError(f"TomTom request failed with HTTP {response.status_code}") from None

        payload = response.json()
        flow = payload["flowSegmentData"]
        return TrafficFlowResponse(
            road_sample_id=road_sample.road_sample_id,
            # TomTom returns a current snapshot without a source event timestamp.
            observed_at=received_at,
            received_at=received_at,
            current_speed_kph=int(flow["currentSpeed"]),
            free_flow_speed_kph=int(flow["freeFlowSpeed"]),
            current_travel_time_seconds=int(flow["currentTravelTime"]),
            free_flow_travel_time_seconds=int(flow["freeFlowTravelTime"]),
            confidence=float(flow["confidence"]),
            road_closure=bool(flow["roadClosure"]),
            request_fingerprint=request_fingerprint,
            response_sha256=hashlib.sha256(response.content).hexdigest(),
            http_status=response.status_code,
        )
