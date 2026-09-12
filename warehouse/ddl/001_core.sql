CREATE DATABASE IF NOT EXISTS control;
CREATE DATABASE IF NOT EXISTS warehouse;
CREATE DATABASE IF NOT EXISTS quality;
CREATE DATABASE IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS control.ingestion_run
(
    run_id UUID,
    source_id LowCardinality(String),
    status LowCardinality(String),
    started_at DateTime64(3, 'UTC'),
    completed_at Nullable(DateTime64(3, 'UTC')),
    records_received UInt32 DEFAULT 0,
    records_inserted UInt32 DEFAULT 0,
    records_quarantined UInt32 DEFAULT 0,
    error_message Nullable(String),
    code_version String,
    updated_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (source_id, started_at, run_id);

CREATE TABLE IF NOT EXISTS control.raw_evidence
(
    evidence_id UUID,
    run_id UUID,
    source_id LowCardinality(String),
    city_id LowCardinality(String),
    request_fingerprint FixedString(64),
    response_sha256 FixedString(64),
    received_at DateTime64(3, 'UTC'),
    payload_uri Nullable(String),
    retention_policy LowCardinality(String),
    http_status UInt16
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(received_at)
ORDER BY (source_id, city_id, received_at, request_fingerprint);

CREATE TABLE IF NOT EXISTS warehouse.dim_city
(
    city_id LowCardinality(String),
    city_name String,
    country_code FixedString(3),
    country_name String,
    timezone String,
    currency_code FixedString(3),
    valid_from Date,
    valid_to Nullable(Date),
    boundary_version String
)
ENGINE = ReplacingMergeTree
ORDER BY (city_id, valid_from);

CREATE TABLE IF NOT EXISTS warehouse.dim_source
(
    source_id LowCardinality(String),
    source_name String,
    domain LowCardinality(String),
    refresh_cadence String,
    observation_grain String,
    retention_policy String,
    attribution_required Bool,
    contract_version String,
    valid_from Date
)
ENGINE = ReplacingMergeTree
ORDER BY (source_id, contract_version, valid_from);

CREATE TABLE IF NOT EXISTS warehouse.dim_road_sample
(
    road_sample_id LowCardinality(String),
    city_id LowCardinality(String),
    label String,
    latitude Decimal(9, 6),
    longitude Decimal(9, 6),
    selection_rule String,
    valid_from Date,
    valid_to Nullable(Date)
)
ENGINE = ReplacingMergeTree
ORDER BY (city_id, road_sample_id, valid_from);

CREATE TABLE IF NOT EXISTS warehouse.fact_traffic_flow_observation
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    city_id LowCardinality(String),
    road_sample_id LowCardinality(String),
    collection_slot DateTime('UTC'),
    observed_at DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    current_speed_kph UInt16,
    free_flow_speed_kph UInt16,
    current_travel_time_seconds UInt32,
    free_flow_travel_time_seconds UInt32,
    confidence Float32,
    road_closure Bool,
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(collection_slot)
ORDER BY (city_id, road_sample_id, collection_slot, observation_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_weather_observation
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    city_id LowCardinality(String),
    observed_at DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    temperature_celsius Float32,
    precipitation_mm Float32,
    wind_speed_kph Float32,
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(observed_at)
ORDER BY (city_id, observed_at, observation_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_air_quality_observation
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    city_id LowCardinality(String),
    observed_at DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    pm2_5_micrograms_per_cubic_metre Float32,
    pm10_micrograms_per_cubic_metre Float32,
    nitrogen_dioxide_micrograms_per_cubic_metre Float32,
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(observed_at)
ORDER BY (city_id, observed_at, observation_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_fx_rate
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    base_currency FixedString(3),
    quote_currency FixedString(3),
    observed_at DateTime64(3, 'UTC'),
    received_at DateTime64(3, 'UTC'),
    rate_quote_per_base Decimal(18, 6),
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(observed_at)
ORDER BY (quote_currency, observed_at, observation_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_commercial_poi_snapshot
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    city_id LowCardinality(String),
    snapshot_at DateTime64(3, 'UTC'),
    category LowCardinality(String),
    poi_count UInt32,
    area_definition String,
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY toYYYYMM(snapshot_at)
ORDER BY (city_id, category, snapshot_at, observation_key);

CREATE TABLE IF NOT EXISTS warehouse.fact_economic_indicator_release
(
    observation_key FixedString(64),
    source_id LowCardinality(String),
    run_id UUID,
    country_code FixedString(3),
    indicator_code LowCardinality(String),
    indicator_name String,
    reference_year UInt16,
    value Float64,
    received_at DateTime64(3, 'UTC'),
    response_sha256 FixedString(64),
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(ingested_at)
PARTITION BY reference_year
ORDER BY (country_code, indicator_code, reference_year, observation_key);

CREATE TABLE IF NOT EXISTS quality.rule_result
(
    result_id UUID,
    run_id UUID,
    source_id LowCardinality(String),
    city_id LowCardinality(String),
    rule_id LowCardinality(String),
    severity LowCardinality(String),
    outcome LowCardinality(String),
    observed_at DateTime64(3, 'UTC'),
    numerator UInt32,
    denominator UInt32,
    reason Nullable(String),
    evidence_id Nullable(UUID)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(observed_at)
ORDER BY (source_id, city_id, rule_id, observed_at, result_id);

CREATE TABLE IF NOT EXISTS mart.city_mobility_daily
(
    city_id LowCardinality(String),
    local_date Date,
    observations UInt32,
    valid_observations UInt32,
    valid_sample_coverage_pct Float32,
    median_current_speed_kph Float32,
    median_free_flow_speed_kph Float32,
    median_congestion_ratio Float32,
    average_confidence Float32,
    freshest_observation_at DateTime64(3, 'UTC'),
    refreshed_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(refreshed_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (city_id, local_date);

CREATE TABLE IF NOT EXISTS mart.city_climate_environment_daily
(
    city_id LowCardinality(String),
    local_date Date,
    weather_observations UInt32,
    air_quality_observations UInt32,
    average_temperature_celsius Float32,
    total_precipitation_mm Float32,
    average_wind_speed_kph Float32,
    average_pm2_5_micrograms_per_cubic_metre Float32,
    average_pm10_micrograms_per_cubic_metre Float32,
    average_nitrogen_dioxide_micrograms_per_cubic_metre Float32,
    freshest_observation_at DateTime64(3, 'UTC'),
    refreshed_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(refreshed_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (city_id, local_date);

CREATE TABLE IF NOT EXISTS mart.city_economic_daily
(
    city_id LowCardinality(String),
    local_date Date,
    currency_code FixedString(3),
    usd_rate Float64,
    fx_observation_count UInt32,
    latest_country_inflation_pct Nullable(Float64),
    latest_country_inflation_year Nullable(UInt16),
    freshest_observation_at DateTime64(3, 'UTC'),
    refreshed_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(refreshed_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (city_id, local_date);

CREATE TABLE IF NOT EXISTS mart.city_intelligence_daily
(
    city_id LowCardinality(String),
    local_date Date,
    mobility_component Nullable(Float32),
    commercial_component Nullable(Float32),
    environment_component Nullable(Float32),
    market_component Nullable(Float32),
    direction_component Nullable(Float32),
    weighted_coverage_pct Float32,
    score_confidence_pct Float32,
    score_status LowCardinality(String),
    city_intelligence_score Nullable(Float32),
    formula_version LowCardinality(String),
    limitation String,
    refreshed_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(refreshed_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (city_id, local_date);
