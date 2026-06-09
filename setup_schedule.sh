#!/bin/bash
#
# Install (or refresh) the launchd jobs that run the unattended data refresh.
# Idempotent: re-running re-installs and reloads. Run once: ./setup_schedule.sh
#
#   monthly   (1st, 06:00)                  -> refresh.sh locations  (locations + ratings)
#   quarterly (1st of Jan/Apr/Jul/Oct, 07:00) -> refresh.sh sba       (SBA 7(a) loans)
#   annual    (May 1, 08:00)                -> refresh.sh fdd         (FDD ownership)
#
# LaunchAgents run in your user session, so git's osxkeychain credential helper
# works for `git push` whenever you're logged in. Jobs missed while the Mac is
# asleep/off run at the next wake.

set -e
REPO="$(cd "$(dirname "$0")" && pwd)"
RUN="$REPO/refresh.sh"
LA="$HOME/Library/LaunchAgents"
UID_N="$(id -u)"
mkdir -p "$LA" "$REPO/logs"
chmod +x "$RUN"

emit(){  # emit <label> <mode> <calendar-xml>
  local label="$1" mode="$2" cal="$3" plist="$LA/$1.plist"
  cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$RUN</string><string>$mode</string></array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>StandardOutPath</key><string>$REPO/logs/launchd-$mode.out</string>
  <key>StandardErrorPath</key><string>$REPO/logs/launchd-$mode.err</string>
  <key>RunAtLoad</key><false/>
  <key>StartCalendarInterval</key>
$cal
</dict></plist>
PLIST
  launchctl bootout "gui/$UID_N/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$UID_N" "$plist"
  echo "installed: $label -> refresh.sh $mode"
}

emit "com.alloymap.monthly" "locations" \
'  <dict><key>Day</key><integer>1</integer><key>Hour</key><integer>6</integer><key>Minute</key><integer>0</integer></dict>'

emit "com.alloymap.quarterly" "sba" \
'  <array>
    <dict><key>Month</key><integer>1</integer><key>Day</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Month</key><integer>4</integer><key>Day</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Month</key><integer>7</integer><key>Day</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
    <dict><key>Month</key><integer>10</integer><key>Day</key><integer>1</integer><key>Hour</key><integer>7</integer><key>Minute</key><integer>0</integer></dict>
  </array>'

emit "com.alloymap.annual" "fdd" \
'  <dict><key>Month</key><integer>5</integer><key>Day</key><integer>1</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>'

echo
echo "Loaded jobs:"
launchctl list | grep -i alloymap || echo "  (none found — check errors above)"
