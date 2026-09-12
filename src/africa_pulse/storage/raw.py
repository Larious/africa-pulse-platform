import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from africa_pulse.settings import PROJECT_ROOT


def persist_json_payload(source_id: str, payload: dict[str, Any], received_at: datetime) -> tuple[str, str]:
    """Write immutable JSON evidence under an ignored path and return URI plus checksum."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    checksum = hashlib.sha256(canonical).hexdigest()
    timestamp = received_at.astimezone(UTC)
    relative = Path("data/raw") / f"source={source_id}" / f"received_date={timestamp:%Y-%m-%d}" / f"{checksum}.json"
    destination = PROJECT_ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(canonical)
    return str(relative), checksum
