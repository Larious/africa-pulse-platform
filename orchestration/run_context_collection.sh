#!/usr/bin/env bash
set -euo pipefail

# Weekly commercial context snapshot.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

.venv/bin/python -m africa_pulse.orchestration.context_collection --commercial
.venv/bin/python -m africa_pulse.orchestration.refresh_marts
