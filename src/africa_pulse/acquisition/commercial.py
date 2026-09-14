import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from africa_pulse.config import City

SOURCE_ID = "openstreetmap_overpass_commercial_v1"
URL = "https://overpass-api.de/api/interpreter"


@dataclass(frozen=True)
class CommercialSnapshot:
    snapshot_at: datetime
    received_at: datetime
    category_counts: dict[str, int]
    request_fingerprint: str
    payload: dict


class OverpassCommercialClient:
    def __init__(self, timeout_seconds: float = 90.0, max_attempts: int = 3) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts

    def fetch_snapshot(self, city: City) -> CommercialSnapshot:
        bbox = city.commercial_snapshot_bbox
        bbox_text = f"{bbox.south},{bbox.west},{bbox.north},{bbox.east}"
        query = (
            "[out:json][timeout:60];"
            f"(nwr[\"shop\"]({bbox_text});"
            f"nwr[\"amenity\"~\"restaurant|cafe|bank|pharmacy\"]({bbox_text}););"
            "out center tags;"
        )
        received_at = datetime.now(UTC)
        response = self._post_with_retries(query)
        payload = response.json()
        counts = {"shop": 0, "restaurant": 0, "cafe": 0, "bank": 0, "pharmacy": 0}
        seen = set()
        for element in payload.get("elements", []):
            element_id = (element.get("type"), element.get("id"))
            if element_id in seen:
                continue
            seen.add(element_id)
            tags = element.get("tags", {})
            if "shop" in tags:
                counts["shop"] += 1
            amenity = tags.get("amenity")
            if amenity in counts:
                counts[amenity] += 1
        fingerprint = hashlib.sha256(json.dumps({"source": SOURCE_ID, "bbox": bbox_text}, sort_keys=True).encode()).hexdigest()
        return CommercialSnapshot(received_at, received_at, counts, fingerprint, payload)

    def _post_with_retries(self, query: str) -> httpx.Response:
        headers = {"User-Agent": "AfricaPulseCapstone/0.1 (educational data engineering project)"}
        for attempt in range(1, self._max_attempts + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(URL, data={"data": query}, headers=headers)
                    response.raise_for_status()
                    return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as error:
                response = getattr(error, "response", None)
                retryable_status = getattr(response, "status_code", 0) in {429, 500, 502, 503, 504}
                if attempt == self._max_attempts or (isinstance(error, httpx.HTTPStatusError) and not retryable_status):
                    raise
                time.sleep(attempt)
        raise AssertionError("retry loop must return or raise")
