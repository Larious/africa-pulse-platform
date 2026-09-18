# Warehouse Model

## Conformed concepts

`dim_city` defines the city ID, timezone, currency, and boundary version used by every city-level fact. `dim_source` records source contract metadata. `dim_road_sample` records the selected traffic reference locations. All source facts carry source ID, run ID, received time, response checksum, and a deterministic observation key. `control.ingestion_run` and `control.raw_evidence` are the operational and provenance tables; `quality.rule_result` records validation outcomes before publication.

## Facts

| Fact | Grain | Historical policy |
|---|---|---|
| `fact_traffic_flow_observation` | One TomTom response for one road sample in a two-hour slot | Latest correction for the same observation key wins through `ReplacingMergeTree`. |
| `fact_weather_observation` | One weather snapshot for one city reference coordinate and source time | Source observations are retained by month. |
| `fact_air_quality_observation` | One modelled pollutant snapshot for one city reference coordinate and source time | Source observations are retained by month. |
| `fact_fx_rate` | One USD-to-quote-currency snapshot for one two-hour slot | Source observations are retained by month. |
| `fact_commercial_poi_snapshot` | One category count for one candidate area and snapshot | Candidate boundary version remains in `area_definition`. |
| `fact_economic_indicator_release` | One country indicator release for a reference year | A later source release is a new arrival, not a rewrite of its reference period. |

Dimensions are latest-state reference tables at this milestone. If road sample selection, city boundaries, or source contracts change, a new effective-dated row is inserted; prior facts retain their original foreign-key values and boundary version.

The natural keys are `city_id` for a city, `road_sample_id` for a sampled location, and `source_id` for a connector contract. Facts link to those IDs and retain their own observation identity, so changing a dimension version does not rewrite historical observations.

## Marts

Each mart has grain `one city, one local analytical day`. `city_mobility_daily`, `city_climate_environment_daily`, and `city_economic_daily` aggregate source facts into consumer fields. `city_intelligence_daily` joins available components, reports weighted coverage, and withholds a numeric score when its published eligibility rules are not met.

## ClickHouse design

Time-series facts partition monthly and order by city plus source-specific time and observation identity. This aligns with city-and-date analysis, bounded reprocessing, and deterministic deduplication. Daily marts use `ReplacingMergeTree(refreshed_at)` so rerunning mart refresh replaces the same city-day result instead of multiplying it.
