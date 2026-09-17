#!/usr/bin/env bash
set -euo pipefail

# Every two hours: traffic, weather, air quality, FX, then dependent daily marts.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

.venv/bin/python -m africa_pulse.orchestration.tomtom_collection
.venv/bin/python -m africa_pulse.orchestration.public_collection
.venv/bin/python -m africa_pulse.orchestration.refresh_marts
