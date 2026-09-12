import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

SOURCE_ID = "exchange_rate_api_usd_v6"
URL = "https://open.er-api.com/v6/latest/USD"


@dataclass(frozen=True)
class FxResponse:
    observed_at: datetime
    received_at: datetime
    rates: dict[str, float]
    request_fingerprint: str
    payload: dict


class ExchangeRateClient:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._timeout_seconds = timeout_seconds

    def fetch_usd_rates(self, target_currencies: set[str]) -> FxResponse:
        received_at = datetime.now(UTC)
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.get(URL)
            response.raise_for_status()
        payload = response.json()
        if payload.get("result") != "success":
            raise RuntimeError(f"ExchangeRate-API did not return success: {payload.get('result')}")
        rates = {currency: float(payload["rates"][currency]) for currency in target_currencies}
        return FxResponse(
            observed_at=received_at,
            received_at=received_at,
            rates=rates,
            request_fingerprint=hashlib.sha256(json.dumps({"source": SOURCE_ID, "base": "USD"}).encode()).hexdigest(),
            payload=payload,
        )
