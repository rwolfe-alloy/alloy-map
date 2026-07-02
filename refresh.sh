#!/bin/bash
#
# Unattended data refresh for the Alloy map. Run by launchd (see launchd/).
#
#   ./refresh.sh locations   # monthly  — re-scrape locations + Google ratings
#   ./refresh.sh sba         # quarterly — re-pull SBA 7(a) loans
#   ./refresh.sh fdd         # annual   — re-pull FDD franchisee ownership
#   ./refresh.sh market      # manual/annual — Census demographics + competitor density
#
# Each mode rebuilds index.html and, IF tracked data changed, commits + pushes
# to main (GitHub Pages auto-deploys). All output is logged; a failing step
# aborts before any push so a broken scrape never overwrites good data.

set -o pipefail
# launchd runs with a minimal environment — pin PATH so git/curl/gh/python resolve.
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# stream python output to the log live (else block-buffering makes a running job look hung)
export PYTHONUNBUFFERED=1
cd "$(dirname "$0")" || exit 1
MODE="${1:?usage: refresh.sh [locations|sba|fdd]}"
mkdir -p logs
LOG="logs/refresh-$MODE-$(date +%Y%m%d-%H%M%S).log"
PY=/usr/local/bin/python3        # the interpreter that has pdfplumber installed

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }
notify(){ osascript -e "display notification \"$2\" with title \"Alloy Map · $1\"" 2>/dev/null || true; }
run(){ log "RUN: $*"; "$@" >>"$LOG" 2>&1 || { log "FAILED ($?): $*"; notify "refresh $MODE FAILED" "$* — see $LOG"; exit 1; }; }

log "=== refresh '$MODE' starting ==="

case "$MODE" in
  locations)
    run $PY scrape_locations.py
    run $PY fetch_ratings.py            # needs .apikey
    ;;
  sba)
    # Resolve the current FY2020-present CSV url (filename carries an "as-of" date
    # that changes each quarter; the resource id is stable).
    RID="d67d3ccb-2002-4134-a288-481b51cd3479"
    SBA_URL=$(curl -s --connect-timeout 20 --max-time 30 "https://data.sba.gov/api/3/action/resource_show?id=$RID" \
              | $PY -c "import sys,json;print(json.load(sys.stdin)['result']['url'])" 2>>"$LOG")
    [ -z "$SBA_URL" ] && { log "Could not resolve SBA CSV url from CKAN API."; exit 1; }
    log "SBA CSV: $SBA_URL"
    run curl -s -L --connect-timeout 20 --max-time 900 "$SBA_URL" -o _sba_7a.csv
    run $PY match_sba.py
    ;;
  fdd)
    run $PY fetch_fdd.py
    run $PY parse_fdd.py
    run $PY match_owners.py
    $PY parse_item19.py alloy_fdd_latest.pdf >>"$LOG" 2>&1 || log "WARN: Item 19 parse failed (keeping previous)."
    $PY parse_churn.py   alloy_fdd_latest.pdf >>"$LOG" 2>&1 || log "WARN: churn parse failed (keeping previous)."
    $PY parse_pipeline.py alloy_fdd_latest.pdf >>"$LOG" 2>&1 || log "WARN: pipeline parse failed (keeping previous)."
    ;;
  market)
    run $PY fetch_demographics.py
    run $PY fetch_competitors.py        # needs .apikey
    ;;
  *) log "unknown mode '$MODE'"; exit 2 ;;
esac

# Snapshot + changelog of what changed (vs last committed version), before rebuild
run $PY snapshot.py "$(date '+%Y-%m-%d')"
# Distill snapshots into trend data (needs 2+ snapshots; harmless no-op before that)
$PY build_trends.py >>"$LOG" 2>&1 || log "WARN: trend build failed (keeping previous)."

# Validation gate — a failure here aborts before anything is committed/pushed
run $PY validate.py

run $PY rebuild_index.py

# Commit + push only if tracked data actually changed
git add alloy_enriched.json alloy_sba_loans.json alloy_item19.json alloy_churn.json alloy_trends.json alloy_demog.json alloy_competitors.json alloy_pipeline.json index.html CHANGELOG.md snapshots 2>/dev/null
if git diff --cached --quiet; then
  log "No data changes — nothing to commit."
elif [ -n "$DRY_RUN" ]; then
  log "DRY_RUN: data changed — would commit + push:"
  git diff --cached --stat | tee -a "$LOG"
  git reset -q   # leave the working tree changes, just unstage
else
  MSG="Auto-refresh ($MODE): $(date '+%Y-%m-%d')"
  git commit -q -m "$MSG" >>"$LOG" 2>&1
  if git push origin main >>"$LOG" 2>&1; then
    log "Committed + pushed: $MSG"; notify "refreshed ($MODE)" "$MSG — deployed"
  else
    log "Commit made but PUSH FAILED — will retry next run."; notify "refresh $MODE: push failed" "committed locally; will retry"
  fi
fi
log "=== refresh '$MODE' done ==="
