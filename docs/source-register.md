# Source Register

| Source ID | Domain | Access | Grain | Refresh | Important limitation |
|---|---|---|---|---|---|
| `tomtom_traffic_flow_v4` | Mobility | API key | One response per selected road sample and two-hour slot | Every 2 hours | A road-flow congestion proxy; it is not ridership, passenger demand, or fare revenue. Full payload retention awaits terms review. |
| `open_meteo_weather_v1` | Climate | Public HTTPS API | One current weather snapshot at a city reference coordinate | Every 2 hours | A coordinate-based model estimate cannot represent all conditions across a city. |
| `open_meteo_air_quality_v1` | Environment | Public HTTPS API | One current modelled air-quality snapshot at a city reference coordinate | Every 2 hours | Modelled concentrations are not ground-station readings. |
| `exchange_rate_api_usd_v6` | Market | Public HTTPS API | One USD-to-NGN or USD-to-ZAR rate snapshot | Every 2 hours | Current snapshots establish history from platform launch; they do not create a long historical series retrospectively. |

## Access and evidence policy

Every request records its source ID, run ID, request fingerprint, response checksum, received time, and HTTP status in `control.raw_evidence`. Open public-source payloads are stored under ignored `data/raw/` paths. TomTom's full payload is not stored until the applicable account terms permit it; its normalised measures and evidence metadata remain traceable.

## City portfolio

Lagos and Abuja use `Africa/Lagos` with NGN. Cape Town uses `Africa/Johannesburg` with ZAR. A city is configured by its canonical ID, timezone, currency, reference coordinate, and road samples, so adding a city changes configuration before it changes pipeline code.
