#!/usr/bin/env bash
set -euo pipefail

# Invoke this script from cron every two hours; it exits on the first failed source run.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

.venv/bin/python -m africa_pulse.orchestration.tomtom_collection
.venv/bin/python -m africa_pulse.orchestration.public_collection
.venv/bin/python -m africa_pulse.orchestration.context_collection
.venv/bin/python -m africa_pulse.orchestration.refresh_marts
