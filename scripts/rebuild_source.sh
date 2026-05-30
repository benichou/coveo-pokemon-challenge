#!/usr/bin/env bash
#
# Trigger a rebuild of the pokemondb-sitemap source and wait for it to finish.
#
# Use this after editing mappings, web scraping config, URL rules, or any
# source-level setting that needs the index to refresh. For a single-Pokemon
# test source, the rebuild completes in <30s.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_SITEMAP_SOURCE_ID
#   COVEO_ADMIN_API_KEY     (needs Content > Sources > Edit)
#
# Usage:
#   scripts/rebuild_source.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_SITEMAP_SOURCE_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env (needs Content > Sources > Edit)}"

SOURCE_URL="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${COVEO_SITEMAP_SOURCE_ID}"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

echo "Triggering rebuild of pokemondb-sitemap..."
http_code=$(
  curl -sS -o /tmp/_rebuild_resp.json -w "%{http_code}" \
    -X POST -H "$AUTH_HEADER" \
    "${SOURCE_URL}/rebuild"
)

if [[ "$http_code" != "200" && "$http_code" != "201" && "$http_code" != "202" && "$http_code" != "204" ]]; then
  echo "  ✗ Rebuild request failed (HTTP $http_code):" >&2
  cat /tmp/_rebuild_resp.json >&2
  echo "" >&2
  rm -f /tmp/_rebuild_resp.json
  exit 1
fi
rm -f /tmp/_rebuild_resp.json
echo "  ✓ Rebuild queued."
echo ""

echo "Polling source status until idle..."
max_attempts=60   # ~5 minutes at 5s intervals
attempt=0
seen_non_idle=false   # avoid catching IDLE before the rebuild has even started

while (( attempt < max_attempts )); do
  attempt=$((attempt + 1))
  status_payload=$(curl -sS -H "$AUTH_HEADER" "$SOURCE_URL")
  src_status=$(
    echo "$status_payload" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('information', {}).get('sourceStatus', {}).get('type', 'UNKNOWN'))
"
  )
  items=$(
    echo "$status_payload" | python3 -c "
import json, sys
d = json.load(sys.stdin)
n = d.get('information', {}).get('numberOfDocuments')
print(n if n is not None else '?')
"
  )

  printf "  [%02d] status=%s items=%s\n" "$attempt" "$src_status" "$items"

  if [[ "$src_status" == "ERROR" ]]; then
    echo "" >&2
    echo "Rebuild failed with ERROR status." >&2
    exit 1
  fi

  if [[ "$src_status" != "IDLE" ]]; then
    seen_non_idle=true
  elif [[ "$seen_non_idle" == "true" ]]; then
    # We saw the source go busy and now it's back to IDLE — that's a real completion.
    echo ""
    echo "Rebuild complete."
    echo "  Items indexed: $items"
    exit 0
  fi
  # else: IDLE but we haven't seen the operation start yet — keep waiting.

  sleep 5
done

echo "" >&2
echo "Timed out after $max_attempts polls. Check the Activity tab in the Admin Console." >&2
exit 1
