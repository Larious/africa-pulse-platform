# Reproducibility Check

## Verified on 2026-09-14

A clean clone of `https://github.com/Larious/africa-pulse-platform.git` was created outside the working directory. A new Python environment installed `.[dev]`, then completed `pytest -q` and `ruff check .` successfully. The dashboard module imported without a TomTom key. The presentation dependency is now declared under the `presentation` extra and is checked in GitHub Actions.

The clean installation correctly rejected TomTom ingestion without `TOMTOM_API_KEY`, with a clear error message. This proves a read-only warehouse consumer does not need the collection credential while ingestion does.

## Remaining environment check

An isolated ClickHouse startup was verified with ports `18123` and `19000`. It created the `control`, `warehouse`, `quality`, and `mart` databases from repository DDL; an empty mart refresh and dashboard query both completed. `docker-compose.yml` supports `CLICKHOUSE_HTTP_PORT` and `CLICKHOUSE_NATIVE_PORT` overrides. A final assessor demonstration should configure a legitimate TomTom key only in that clone's ignored `.env` and retain the command output.
