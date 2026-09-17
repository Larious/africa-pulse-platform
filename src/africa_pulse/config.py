from dataclasses import dataclass
from pathlib import Path

import yaml

from africa_pulse.settings import PROJECT_ROOT


@dataclass(frozen=True)
class RoadSample:
    road_sample_id: str
    label: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class BoundingBox:
    south: float
    west: float
    north: float
    east: float


@dataclass(frozen=True)
class City:
    city_id: str
    city_name: str
    country_code: str
    country_name: str
    timezone: str
    currency_code: str
    reference_latitude: float
    reference_longitude: float
    commercial_snapshot_bbox: BoundingBox
    road_samples: tuple[RoadSample, ...]


def load_cities(path: Path | None = None) -> tuple[City, ...]:
    config_path = path or PROJECT_ROOT / "config" / "cities.yaml"
    payload = yaml.safe_load(config_path.read_text())
    return tuple(
        City(
            city_id=city["city_id"],
            city_name=city["city_name"],
            country_code=city["country_code"],
            country_name=city["country_name"],
            timezone=city["timezone"],
            currency_code=city["currency_code"],
            reference_latitude=city["reference_latitude"],
            reference_longitude=city["reference_longitude"],
            commercial_snapshot_bbox=BoundingBox(**city["commercial_snapshot_bbox"]),
            road_samples=tuple(RoadSample(**sample) for sample in city["road_samples"]),
        )
        for city in payload["cities"]
    )
