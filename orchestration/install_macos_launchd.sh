#!/usr/bin/env bash
set -euo pipefail

# Install per-user schedules without storing an absolute project path in Git.
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
agent_dir="$HOME/Library/LaunchAgents"
log_dir="$project_dir/logs"
mkdir -p "$agent_dir" "$log_dir"

write_agent() {
  local label="$1"
  local interval="$2"
  local command="$3"
  local plist="$agent_dir/$label.plist"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array><string>/bin/zsh</string><string>$project_dir/$command</string></array>
  <key>StartInterval</key><integer>$interval</integer>
  <key>WorkingDirectory</key><string>$project_dir</string>
  <key>StandardOutPath</key><string>$log_dir/$label.log</string>
  <key>StandardErrorPath</key><string>$log_dir/$label.error.log</string>
</dict></plist>
EOF
  launchctl bootout "gui/$(id -u)" "$plist" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$plist"
}

write_agent "com.africa-pulse.fast" 7200 "orchestration/run_fast_collections.sh"
write_agent "com.africa-pulse.commercial" 604800 "orchestration/run_context_collection.sh"
write_agent "com.africa-pulse.economic" 2592000 "orchestration/run_economic_collection.sh"
echo "Installed Africa Pulse schedules. Use launchctl print gui/$(id -u)/com.africa-pulse.fast to inspect status."
