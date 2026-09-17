import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

SOURCE_ID = "world_bank_indicators_v2"
BASE_URL = "https://api.worldbank.org/v2/country"
INDICATORS = ("PA.NUS.FCRF", "FP.CPI.TOTL.ZG")


@dataclass(frozen=True)
class EconomicRelease:
    country_code: str
    indicator_code: str
    indicator_name: str
    reference_year: int
    value: float


@dataclass(frozen=True)
class WorldBankResponse:
    received_at: datetime
    releases: tuple[EconomicRelease, ...]
    request_fingerprint: str
    payload: dict


class WorldBankClient:
    def fetch_indicators(self, country_codes: set[str]) -> WorldBankResponse:
        received_at = datetime.now(UTC)
        all_payloads, releases = [], []
        with httpx.Client(timeout=30.0) as client:
            for indicator in INDICATORS:
                response = client.get(
                    f"{BASE_URL}/{';'.join(sorted(country_codes))}/indicator/{indicator}",
                    params={"format": "json", "per_page": 100},
                )
                response.raise_for_status()
                payload = response.json()
                all_payloads.append(payload)
                for record in payload[1] or []:
                    if record["value"] is None:
                        continue
                    releases.append(EconomicRelease(
                        country_code=record["countryiso3code"], indicator_code=indicator,
                        indicator_name=record["indicator"]["value"], reference_year=int(record["date"]), value=float(record["value"]),
                    ))
        payload = {"responses": all_payloads}
        fingerprint = hashlib.sha256(json.dumps({"source": SOURCE_ID, "countries": sorted(country_codes), "indicators": INDICATORS}, sort_keys=True).encode()).hexdigest()
        return WorldBankResponse(received_at, tuple(releases), fingerprint, payload)
