#!/usr/bin/env bash
set -euo pipefail

# Backwards-compatible fast collection entrypoint. Commercial and economic jobs have separate cadences.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

exec "$project_dir/orchestration/run_fast_collections.sh"
