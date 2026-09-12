-- Run health: show latest state for each source execution.
SELECT
    source_id,
    status,
    started_at,
    completed_at,
    records_received,
    records_inserted,
    records_quarantined,
    error_message
FROM control.ingestion_run FINAL
ORDER BY started_at DESC;

-- Freshness: source observation time compared with the query time.
SELECT 'traffic' AS domain, max(observed_at) AS freshest_observation_at, dateDiff('minute', freshest_observation_at, now()) AS age_minutes
FROM warehouse.fact_traffic_flow_observation FINAL
UNION ALL
SELECT 'weather', max(observed_at), dateDiff('minute', max(observed_at), now())
FROM warehouse.fact_weather_observation FINAL
UNION ALL
SELECT 'air_quality', max(observed_at), dateDiff('minute', max(observed_at), now())
FROM warehouse.fact_air_quality_observation FINAL
UNION ALL
SELECT 'fx', max(observed_at), dateDiff('minute', max(observed_at), now())
FROM warehouse.fact_fx_rate FINAL;

-- Data-quality outcomes: failed checks indicate records that were withheld or need investigation.
SELECT source_id, city_id, rule_id, severity, outcome, count() AS result_count, max(observed_at) AS latest_result_at
FROM quality.rule_result
GROUP BY source_id, city_id, rule_id, severity, outcome
ORDER BY outcome DESC, latest_result_at DESC;

-- Duplicate check: each natural traffic observation must have one surviving record after deduplication.
SELECT city_id, road_sample_id, collection_slot, count() AS physical_rows
FROM warehouse.fact_traffic_flow_observation FINAL
GROUP BY city_id, road_sample_id, collection_slot
HAVING physical_rows > 1;
