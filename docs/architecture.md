# Architecture Decision Record: Initial Vertical Slice

## Scope

The first implemented source is TomTom Traffic Flow, configured for Lagos, Abuja, and Cape Town. It was selected for its consistent road-flow schema. The current credential validation returns usable segments for Cape Town; Lagos and Abuja currently return the provider error `Point too far from nearest existing segment`, so those traffic observations remain unavailable until coverage or coordinates are resolved.

## Data path

1. `acquisition/tomtom.py` calls TomTom for each configured road sample.
2. The connector creates a request fingerprint and response hash without placing the API key in logs or tables.
3. `transformation/traffic.py` applies explicit validation rules and calculates congestion only from valid speed values.
4. ClickHouse control tables record run and evidence metadata; the warehouse fact stores the normalised observation.
5. A daily mobility mart will aggregate validated road samples by city and local day.

## Grain

`warehouse.fact_traffic_flow_observation` has one row per provider response for one configured road sample in one two-hour collection slot.

This is a traffic-flow observation, not a passenger journey or a city-wide vehicle count. The daily mart must expose sample coverage and confidence so users understand that it is a sampled congestion proxy.

## Time policy

TomTom Flow Segment Data is a current snapshot and does not return a source event timestamp. `observed_at` is therefore set to the platform retrieval time and documented as an approximation. `received_at` records the same time for this source. If a provider later exposes a source event time, it will be stored separately.

## Retention policy

Until the account terms are reviewed, the platform records request fingerprint, response checksum, status, normalised measures, and provenance metadata. It does not persist the complete TomTom response body. This keeps the platform traceable while avoiding an unsupported assumption about third-party payload retention.

Open-Meteo and ExchangeRate-API payloads use the local immutable `data/raw/` evidence store. The directory is ignored by Git. Its deterministic file name is based on a checksum of canonical JSON, so replay input is stable and a repeated payload does not create a second file.

## Physical design

The traffic fact partitions monthly because queries and backfills naturally filter by month. It orders by `(city_id, road_sample_id, collection_slot, observation_key)` because the expected queries filter by city and time, then compare road samples. A daily mart avoids repeatedly scanning raw traffic facts for executive queries.

## Scale decision

At current scale, one process polls 15 initial validated road samples every two hours. At 10x volume, use independent city/road-sample workers, batched ClickHouse inserts, and a durable work queue; do not start with extra materialized views before a measured performance bottleneck exists.
