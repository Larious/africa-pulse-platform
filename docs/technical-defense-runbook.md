# Technical Defense Runbook

Use this runbook during the capstone defense. It names what to show, the evidence to query, and the claim that evidence supports. It does not create dummy source records.

## Explain the main fact grain

Show `warehouse.fact_traffic_flow_observation` in `warehouse/ddl/001_core.sql`.

State: one row represents one TomTom response for one configured road sample in one two-hour UTC collection slot. `observation_key` is deterministic for that logical event. The grain makes a retry idempotent and lets the daily mart measure how many configured road samples actually contributed.

## Explain ordering and partitioning

Show the traffic table definition and run `analytics/performance_evidence.sql`.

State: the table partitions by collection month, so monthly retention and time-range queries exclude unrelated partitions. It orders by city, road sample, collection slot, and observation key. The common read pattern filters a city and time range, then compares its samples. The daily mart exists so dashboard queries do not repeatedly scan the fact table. At ten times the volume, measure again first; then use worker partitioning and batch inserts before adding a projection or materialized aggregate.

## Trace a dashboard metric

Run this query in ClickHouse:

```sql
SELECT city_id, local_date, median_congestion_ratio, valid_sample_coverage_pct,
       average_confidence, freshest_observation_at
FROM mart.city_mobility_daily FINAL
ORDER BY local_date DESC, city_id;
```

Then trace the same city and day to `warehouse.fact_traffic_flow_observation`, `quality.rule_result`, and `control.raw_evidence` using its `source_id`, road-sample ID, response checksum, and run ID. The complete lineage is in `docs/lineage.md`.

## Demonstrate duplicate handling

Run the TomTom workflow twice within one two-hour slot:

```bash
.venv/bin/python -m africa_pulse.orchestration.tomtom_collection
.venv/bin/python -m africa_pulse.orchestration.tomtom_collection
```

The second run records received responses and evidence, but inserts zero traffic facts for that slot. Confirm it with the duplicate query in `analytics/operational_health.sql`. The expected result is no rows because `fact_exists` checks the deterministic `observation_key` before insertion.

## Demonstrate a source outage and recovery

Show the existing historical evidence rather than inducing an artificial outage:

```sql
SELECT source_id, status, started_at, records_received, records_inserted, error_message
FROM control.ingestion_run FINAL
WHERE source_id = 'openstreetmap_overpass_commercial_v1'
ORDER BY started_at;
```

Explain that the first Overpass run failed with HTTP 406, wrote a `failed` run state, and inserted no facts. The connector was changed to POST with a project user agent; its rerun completed and wrote the commercial snapshots. See ADR-005 in `docs/decision-log.md`. This demonstrates that a failed source is recorded, never silently replaced, and can be safely rerun.

## Explain a late-arriving release

World Bank releases represent country context and may be published after the reference year. The fact stores both `reference_year` and `received_at`. A late release is inserted as evidence of its actual arrival; mart refresh selects the largest available `reference_year` per country with `argMax(value, reference_year)`. It therefore updates the relevant city economic mart on the next refresh without rewriting the original source fact.

State the limitation clearly: current TomTom data is a retrieval-time snapshot, so it cannot demonstrate a provider event arriving late. This behavior is implemented and demonstrated through the World Bank release source, whose source grain contains a real reference period.

## Investigate an instructor-provided anomaly

For a suspected traffic value, identify its source record before changing data:

```sql
SELECT observation_key, run_id, city_id, road_sample_id, collection_slot, observed_at,
       current_speed_kph, free_flow_speed_kph, confidence, response_sha256
FROM warehouse.fact_traffic_flow_observation FINAL
WHERE city_id = 'lagos_ng'
ORDER BY observed_at DESC;
```

Find the associated quality outcomes using `run_id` and `source_id = 'tomtom_traffic_flow_v4'`. Invalid confidence, negative speed, or non-positive free-flow speed fails validation, is written to `quality.rule_result`, and is quarantined before reaching the traffic fact. Do not edit the source fact to hide the anomaly; preserve evidence and document the resolution.

For a changed source field or malformed response, show the failed `control.ingestion_run` record and confirm no normalized fact was created. Review the preserved raw evidence where terms allow, update the connector with a regression test, then rerun the affected interval. `docs/operational-scenarios.md` records the recovery procedure.

## Explain the city score limitation

Run:

```sql
SELECT city_id, weighted_coverage_pct, score_status, city_intelligence_score, limitation
FROM mart.city_intelligence_daily FINAL
ORDER BY city_id;
```

State: the score is intentionally unavailable at 50% weighted coverage. Mobility and environment have observations, but commercial intensity has no approved area/population denominator, market stability needs seven days of FX history, and direction requires 28 days. Publishing a numeric rank now would overstate certainty.
