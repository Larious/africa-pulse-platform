import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from africa_pulse.config import City

WEATHER_SOURCE_ID = "open_meteo_weather_v1"
AIR_QUALITY_SOURCE_ID = "open_meteo_air_quality_v1"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


@dataclass(frozen=True)
class WeatherResponse:
    observed_at: datetime
    received_at: datetime
    temperature_celsius: float
    precipitation_mm: float
    wind_speed_kph: float
    request_fingerprint: str
    payload: dict


@dataclass(frozen=True)
class AirQualityResponse:
    observed_at: datetime
    received_at: datetime
    pm2_5: float
    pm10: float
    nitrogen_dioxide: float
    request_fingerprint: str
    payload: dict


def request_fingerprint(source_id: str, city: City, fields: str) -> str:
    request = {
        "source_id": source_id,
        "latitude": city.reference_latitude,
        "longitude": city.reference_longitude,
        "fields": fields,
        "timezone": "UTC",
    }
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


class OpenMeteoClient:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._timeout_seconds = timeout_seconds

    def fetch_weather(self, city: City) -> WeatherResponse:
        fields = "temperature_2m,precipitation,wind_speed_10m"
        params = {
            "latitude": city.reference_latitude,
            "longitude": city.reference_longitude,
            "current": fields,
            "timezone": "UTC",
        }
        received_at = datetime.now(UTC)
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.get(WEATHER_URL, params=params)
            response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        return WeatherResponse(
            observed_at=datetime.fromisoformat(current["time"]).replace(tzinfo=UTC),
            received_at=received_at,
            temperature_celsius=float(current["temperature_2m"]),
            precipitation_mm=float(current["precipitation"]),
            wind_speed_kph=float(current["wind_speed_10m"]),
            request_fingerprint=request_fingerprint(WEATHER_SOURCE_ID, city, fields),
            payload=payload,
        )

    def fetch_air_quality(self, city: City) -> AirQualityResponse:
        fields = "pm2_5,pm10,nitrogen_dioxide"
        params = {
            "latitude": city.reference_latitude,
            "longitude": city.reference_longitude,
            "current": fields,
            "timezone": "UTC",
        }
        received_at = datetime.now(UTC)
        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.get(AIR_QUALITY_URL, params=params)
            response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        return AirQualityResponse(
            observed_at=datetime.fromisoformat(current["time"]).replace(tzinfo=UTC),
            received_at=received_at,
            pm2_5=float(current["pm2_5"]),
            pm10=float(current["pm10"]),
            nitrogen_dioxide=float(current["nitrogen_dioxide"]),
            request_fingerprint=request_fingerprint(AIR_QUALITY_SOURCE_ID, city, fields),
            payload=payload,
        )
