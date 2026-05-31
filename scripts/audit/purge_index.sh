#!/usr/bin/env bash
#
# scripts/purge_index.sh — apply corrections found by scripts/audit_index.py.
#
# Why this exists
# ---------------
# The audit script identifies non-Pokemon pages that slipped past the URL
# filter. This script is the *durable* fix: it updates config/source/url_filter.json
# so the leak is excluded by the source's filter going forward, then triggers
# a rebuild so the orphan drops out of the index.
#
# Why filter-update is the right pattern for our Sitemap source
# -------------------------------------------------------------
# Coveo's Push API exposes a DELETE-document endpoint, but that surgical
# delete only works for Push sources (Source B in Phase 4). For Sitemap and
# Crawler sources, individual items aren't directly addressable for deletion
# — they're computed from the sitemap on each refresh. If we deleted an
# orphan surgically, the next refresh would re-fetch it because the source
# filter still admits it. The only durable fix is to update the filter.
#
# As a bonus, updating config/source/url_filter.json:
#   - keeps the filter as the single source of truth (the parity test stays
#     meaningful — it reads the same file the source uses);
#   - leaves a git diff that documents *what* we excluded and *why*;
#   - is reversible by reverting the commit.
#
# How it works
# ------------
#   1. Read audit_report.json (default) or take URIs on argv.
#   2. For each leak URL, derive a substring exclusion of the form
#      "/pokedex/<slug>" — this is what we did by hand for /pokedex/shiny.
#   3. Show a diff of the proposed change to config/source/url_filter.json.
#   4. Ask for explicit y/N confirmation.
#   5. On confirm: rewrite url_filter.json, run widen_source.sh all,
#      run rebuild_source.sh.
#
# Usage
#   scripts/purge_index.sh                          # uses audit_report.json
#   scripts/purge_index.sh --report /tmp/leaks.json
#   scripts/purge_index.sh --dry-run                # show diff only
#   scripts/purge_index.sh --uri https://pokemondb.net/pokedex/shiny ...
#
# Required env (sourced from ../.env):
#   COVEO_ORG_ID, COVEO_SITEMAP_SOURCE_ID, COVEO_ADMIN_API_KEY

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FILTER_CONFIG="$REPO_ROOT/config/source/url_filter.json"
DEFAULT_REPORT="$REPO_ROOT/audit_report.json"

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  --report PATH     Path to audit_report.json (default: $DEFAULT_REPORT)
  --uri URL         Add a specific leak URI (repeatable; bypasses report)
  --dry-run         Show the proposed url_filter.json diff, don't apply
  -h, --help        This help
EOF
}

REPORT_PATH="$DEFAULT_REPORT"
DRY_RUN=false
URI_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report) REPORT_PATH="$2"; shift 2 ;;
    --uri)    URI_ARGS+=("$2"); shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

# Collect leak URIs: either from --uri flags, or from audit_report.json.
if [[ ${#URI_ARGS[@]} -gt 0 ]]; then
  LEAK_URIS=("${URI_ARGS[@]}")
else
  if [[ ! -f "$REPORT_PATH" ]]; then
    echo "ERROR: no audit report at $REPORT_PATH" >&2
    echo "Run scripts/audit_index.py first, or pass --uri." >&2
    exit 1
  fi
  # Portable bash 3 substitute for `mapfile -t` (macOS ships bash 3.2).
  LEAK_URIS=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && LEAK_URIS+=("$line")
  done < <(
    REPORT_PATH="$REPORT_PATH" python3 - <<'PY'
import json, os
with open(os.environ['REPORT_PATH']) as f:
    rpt = json.load(f)
for leak in rpt.get('leaks', []):
    print(leak['uri'])
for url in rpt.get('shape_violations', []):
    print(url)
PY
  )
fi

if [[ ${#LEAK_URIS[@]} -eq 0 ]]; then
  echo "No leaks to purge. Index is clean."
  exit 0
fi

echo "Found ${#LEAK_URIS[@]} leak URI(s) to exclude:"
for u in "${LEAK_URIS[@]}"; do
  echo "  - $u"
done

# Compute the diff of url_filter.json (which substrings to add) without
# yet writing the file. The substring shape "/pokedex/<slug>" matches the
# rest of the exclusions_contains list in config/source/url_filter.json.
DIFF_OUTPUT=$(
  URIS="$(printf '%s\n' "${LEAK_URIS[@]}")" \
  FILTER_CONFIG="$FILTER_CONFIG" \
  python3 - <<'PY'
import json, os, sys
uris = [u for u in os.environ['URIS'].splitlines() if u.strip()]
with open(os.environ['FILTER_CONFIG']) as f:
    cfg = json.load(f)
existing = set(cfg['modes']['all']['exclusions_contains'])
to_add = []
for uri in uris:
    # Strip scheme+host → "/pokedex/<slug>". Same shape as the existing
    # entries in exclusions_contains (e.g., "/pokedex/all").
    marker = "pokemondb.net"
    if marker in uri:
        path = uri.split(marker, 1)[1]
    else:
        path = uri
    if path and path not in existing:
        to_add.append(path)
        existing.add(path)  # avoid duplicates within a single run
if not to_add:
    print("NO_CHANGES")
    sys.exit(0)
print("CHANGES")
for s in to_add:
    print(s)
PY
)

if [[ "$DIFF_OUTPUT" == "NO_CHANGES" ]]; then
  echo ""
  echo "All leak URIs are already in config/source/url_filter.json exclusions."
  echo "Nothing to add. (A rebuild may still be needed if orphans persist —"
  echo "in that case, run: scripts/rebuild_source.sh)"
  exit 0
fi

NEW_EXCLUSIONS=$(echo "$DIFF_OUTPUT" | tail -n +2)

echo ""
echo "Proposed addition to config/source/url_filter.json (modes.all.exclusions_contains):"
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  echo "  + \"$line\""
done <<< "$NEW_EXCLUSIONS"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run — config not modified. Re-run without --dry-run to apply."
  exit 0
fi

read -r -p "Apply these changes, then widen + rebuild source? [y/N] " ans
if [[ ! "$ans" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# Apply the change to url_filter.json
echo ""
echo "Updating $FILTER_CONFIG ..."
NEW_EXCL="$NEW_EXCLUSIONS" FILTER_CONFIG="$FILTER_CONFIG" python3 - <<'PY'
import json, os
with open(os.environ['FILTER_CONFIG']) as f:
    cfg = json.load(f)
to_add = [s for s in os.environ['NEW_EXCL'].splitlines() if s.strip()]
cfg['modes']['all']['exclusions_contains'].extend(to_add)
with open(os.environ['FILTER_CONFIG'], 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print(f"  + {len(to_add)} exclusion(s) appended.")
PY

# Re-apply the URL filter to the Coveo source, then rebuild.
echo ""
echo "Applying widened filter to source..."
"$SCRIPT_DIR/widen_source.sh" all

echo ""
echo "Triggering rebuild (this can take 20+ minutes)..."
"$SCRIPT_DIR/rebuild_source.sh"

echo ""
echo "Purge complete."
echo "Re-run scripts/audit_index.py to confirm the index is clean."
echo "Don't forget to commit the updated config/source/url_filter.json."
