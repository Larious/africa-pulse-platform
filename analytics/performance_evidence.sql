-- Baseline executive query. The predicate follows the traffic fact ordering prefix:
-- city_id, then collection_slot. EXPLAIN shows the pruning path used by ClickHouse.
EXPLAIN indexes = 1
SELECT
    city_id,
    toDate(observed_at, 'Africa/Lagos') AS local_date,
    median(1 - current_speed_kph / free_flow_speed_kph) AS median_congestion_ratio
FROM warehouse.fact_traffic_flow_observation FINAL
WHERE city_id = 'lagos_ng'
  AND collection_slot >= toDateTime('2026-09-01 00:00:00', 'UTC')
  AND collection_slot < toDateTime('2026-10-01 00:00:00', 'UTC')
GROUP BY city_id, local_date
ORDER BY local_date;

-- Measure the actual query on the current dataset. Record elapsed time and read_rows
-- from system.query_log only when query logging is enabled in the target environment.
SELECT
    city_id,
    collection_slot,
    road_sample_id,
    current_speed_kph,
    free_flow_speed_kph
FROM warehouse.fact_traffic_flow_observation FINAL
WHERE city_id = 'lagos_ng'
  AND collection_slot >= toDateTime('2026-09-01 00:00:00', 'UTC')
  AND collection_slot < toDateTime('2026-10-01 00:00:00', 'UTC')
ORDER BY collection_slot, road_sample_id;
