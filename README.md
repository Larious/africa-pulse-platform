# Africa Pulse

Africa Pulse is a production-oriented urban-intelligence data platform for Lagos, Abuja, and Cape Town. It combines source data into traceable ClickHouse facts and business marts while exposing data quality, freshness, and provenance.

## Repository map

| Directory | Responsibility |
|---|---|
| `config/` | Versioned city and source configuration; no credentials. |
| `src/africa_pulse/acquisition/` | Source-boundary connectors. |
| `src/africa_pulse/transformation/` | Standardisation, validation, and integration rules. |
| `warehouse/ddl/` | ClickHouse databases, dimensions, facts, quality tables, and marts. |
| `orchestration/` | Scheduled and backfill workflows. |
| `analytics/` | Business queries, dashboard definitions, and metric assets. |
| `presentation/` | Regenerable leadership briefing sourced from live warehouse evidence. |
| `tests/` | Automated unit and integration tests. |
| `docs/` | Architecture, contracts, runbooks, lineage, and decisions. |

## Current milestone

The platform collects traffic, weather, air quality, foreign-exchange, commercial-context, and country-level economic data. TomTom Traffic Flow has validated live coverage in all three cities and provides a sampled congestion metric. The City Intelligence Score stays explicitly unavailable until its history and approved denominators satisfy the published score rules. See `docs/architecture.md` for the table grain, time policy, retention policy, and ClickHouse design rationale.

For a presentation or assessment, use `docs/presentation-defense-guide.md` first, then `docs/technical-defense-runbook.md`. Together they contain the speaking notes, evidence queries, code walkthrough, and precise explanations for fact grain, ClickHouse design, lineage, outages, duplicates, late arrivals, anomalies, and the score limitation.

## Local setup

See `docs/runbook.md`.

The `analytics/business_questions.sql` asset provides the implemented cross-domain questions. Run `analytics/question_readiness.sql` before interpreting results, and read `docs/question-coverage-plan.md` before claiming trend, fuel-economics, population-density, or score conclusions.

## View the live dashboard

After ClickHouse and at least one collection workflow are running, start the read-only local dashboard:

```bash
.venv/bin/python -m africa_pulse.dashboard
```

Open `http://127.0.0.1:8765` in a browser or VS Code's Simple Browser. It reads the ClickHouse marts and control tables every minute; it does not expose credentials or mutate warehouse data.
