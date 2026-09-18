# Runbook: Local Development

## Start ClickHouse

```bash
docker compose up -d
docker compose ps
```

The first startup runs the SQL files in `warehouse/ddl/` and creates the `control`, `warehouse`, `quality`, and `mart` databases.

## Create a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,presentation]'
pytest
ruff check .
```

## Configure secrets

Copy `.env.example` to `.env` and set `TOMTOM_API_KEY`. The local `.env` file is ignored by Git. Never put a key into a YAML file, SQL file, test fixture, log, or report.

## Run the first ingestion workflow

```bash
python -m africa_pulse.orchestration.tomtom_collection
```

The command queries every configured road sample, writes run and evidence metadata, applies three traffic validation rules, and inserts only valid observations. A rerun in the same two-hour collection slot does not create a second fact for the same city and road sample. If TomTom cannot match one point to a covered road segment, that sample is recorded in the run error message, the remaining samples continue, and the run is marked `partial`; partial data must be described with its coverage status.

## Run public-source collection

```bash
python -m africa_pulse.orchestration.public_collection
```

This command runs weather, modelled air quality, and FX as independent source runs. It persists their raw JSON payloads under ignored `data/raw/` paths, records the payload checksums in ClickHouse, validates physical ranges, and inserts normalised facts.

## Run commercial and economic-context collection

```bash
python -m africa_pulse.orchestration.context_collection
```

The commercial workflow records category counts from an OpenStreetMap candidate-area snapshot. The economic workflow records World Bank releases at country grain. Neither source should be described as a direct city-wide commercial census or a city-level economic observation.

## Recovery principle

Every future ingestion command must record a `run_id`, write source evidence metadata, and use a deterministic observation key for the scheduled collection slot. Rerunning a failed slot must update the same logical observation rather than multiply it.

## Monitor and troubleshoot

Run the operational queries in `analytics/operational_health.sql` and `analytics/question_readiness.sql` before interpreting a dashboard result. Inspect `control.ingestion_run` for `running`, `completed`, `partial`, or `failed` status; then use `run_id` to join `control.raw_evidence` and `quality.rule_result`. A `partial` traffic run means some provider points were unavailable and must be reported with coverage. A stale source means its latest observation exceeded the source SLA; rerun the relevant connector only after checking the provider response and rate limits.

## Backfill or replay

The collectors are scheduled snapshot jobs rather than unrestricted historical APIs. To replay a missed interval, restore the source evidence permitted by its terms, run the relevant module with the same configuration, then run `python -m africa_pulse.orchestration.refresh_marts`. Deterministic observation keys make the replay idempotent. Do not create historical observations by copying a current snapshot into an earlier date; if the provider cannot supply the missing period, leave it missing and record the limitation.

## Schedule the collection

Use the supplied macOS installer to create per-user `launchd` schedules. It records output under ignored `logs/` and keeps the absolute project path out of Git.

```bash
chmod +x orchestration/*.sh
./orchestration/install_macos_launchd.sh
launchctl print gui/$(id -u)/com.africa-pulse.fast
```

TomTom, weather, air quality, and FX run every two hours. Commercial snapshots run weekly and World Bank releases monthly. Each job refreshes dependent marts. A scheduler failure is visible in `control.ingestion_run`, and the next scheduled execution can be rerun after the source problem is resolved.

For an isolated local warehouse, choose unused ports before startup:

```bash
CLICKHOUSE_HTTP_PORT=18123 CLICKHOUSE_NATIVE_PORT=19000 docker compose up -d
CLICKHOUSE_PORT=18123 .venv/bin/python -m africa_pulse.orchestration.refresh_marts
```

## Operational evidence

Run [analytics/operational_health.sql](../analytics/operational_health.sql) in ClickHouse to review run outcomes, source freshness, quality failures, and traffic duplicate survivors. Use those query results during the technical defense instead of relying on application logs.

## Open the dashboard

```bash
.venv/bin/python -m africa_pulse.dashboard
```

Open `http://127.0.0.1:8765`. In VS Code, use the Command Palette, select `Simple Browser: Show`, then enter that address. The dashboard is local and read-only. It shows mobility, score coverage, recent runs, and source freshness. A red freshness status means the stored warehouse data is stale; it must not be presented as current.
