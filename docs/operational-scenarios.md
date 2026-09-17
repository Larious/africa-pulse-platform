# Operational Scenarios

## Duplicate collection slot

Run the TomTom workflow twice during the same two-hour slot. The second run records control and quality evidence but inserts zero traffic facts because the deterministic observation key already exists. Confirm with the duplicate query in `analytics/operational_health.sql`.

## Source outage

An actual Overpass HTTP 406 failure and successful POST recovery remain in `control.ingestion_run`. A later 504/429 outage is also retained. The later historical failed run includes partial facts from the implementation that existed at that time; it is intentionally preserved as an audit record. The current commercial workflow buffers all city acquisitions before it writes facts, preventing future partial publication if a city acquisition fails. Preserve failed runs, correct the connector or wait for the provider to recover, then rerun; do not replace missing values with invented observations.

## Late economic release

World Bank facts retain both `reference_year` and `received_at`. A newly published older reference year is stored as a new arrival; `refresh_marts` selects the highest available reference year for city economic context. Run the economic job and mart refresh, then compare the fact and mart records.

## Schema or malformed response

A missing required source field raises an ingestion error before a normalized fact is inserted. The workflow records the failed run and its error message. Preserve the raw response for public sources, update the connector only after reviewing the source change, add a regression test, then rerun the failed interval.

## Interrupted job

All source workflows create a `running` control record before acquisition and write a terminal `completed` or `failed` record. If a process is interrupted externally, investigate the latest `running` run and its evidence rows, then rerun the affected schedule. Deterministic observation keys prevent the recovery from multiplying facts.
