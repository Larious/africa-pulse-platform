import hashlib
import json
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
        with httpx.Client(timeout=90.0) as client:
            response = client.post(
                URL,
                data={"data": query},
                headers={"User-Agent": "AfricaPulseCapstone/0.1 (educational data engineering project)"},
            )
            response.raise_for_status()
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
