#!/usr/bin/env bash
#
# Create the Sitemap source defined in config/source/definition.json.
# Idempotent: if a source with the same name already exists, skip and write
# its ID to .env (so subsequent scripts can find it).
#
# Mutable config managed by other scripts (do NOT include in source_definition.json):
#   - urlFilters → managed by widen_source.sh
#   - scrapingConfiguration → managed by update_scraping_config.sh
#   - mappings → managed by add_mappings.sh
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY   (needs Content > Sources > Edit)
#
# Usage:
#   scripts/create_source.sh
#
# On success, prints the source ID and (if not already there) writes
# COVEO_SITEMAP_SOURCE_ID=<id> to ../.env.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
CONFIG_FILE="$REPO_ROOT/config/source/definition.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: source config not found at $CONFIG_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env}"

SOURCES_URL="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

desired_name=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['name'])")
echo "Desired source name: $desired_name"
echo ""

echo "Fetching existing sources..."
existing_id=$(
  curl -sS -H "$AUTH_HEADER" "$SOURCES_URL" \
    | python3 -c "
import json, sys, os
sources = json.load(sys.stdin)
name = os.environ['DESIRED_NAME']
for s in sources:
    if s.get('name') == name:
        print(s.get('id', ''))
        break
" DESIRED_NAME="$desired_name" 2>/dev/null || true
)
# Re-run to actually capture (env vars on python invocation above are tricky)
existing_id=$(
  DESIRED_NAME="$desired_name" curl -sS -H "$AUTH_HEADER" "$SOURCES_URL" \
    | DESIRED_NAME="$desired_name" python3 -c "
import json, sys, os
sources = json.load(sys.stdin)
for s in sources:
    if s.get('name') == os.environ['DESIRED_NAME']:
        print(s.get('id', ''))
        break
"
)

if [[ -n "$existing_id" ]]; then
  echo "  ✓ Source already exists: $existing_id"
  # If .env doesn't already have COVEO_SITEMAP_SOURCE_ID set to this, mention it.
  if ! grep -q "^COVEO_SITEMAP_SOURCE_ID=$existing_id" "$ENV_FILE" 2>/dev/null; then
    if grep -q "^COVEO_SITEMAP_SOURCE_ID=" "$ENV_FILE"; then
      echo "  ⚠️  .env has a different COVEO_SITEMAP_SOURCE_ID — leaving it untouched. Update manually if needed."
    else
      echo "  Writing COVEO_SITEMAP_SOURCE_ID=$existing_id to .env"
      echo "COVEO_SITEMAP_SOURCE_ID=$existing_id" >> "$ENV_FILE"
    fi
  fi
  exit 0
fi

echo "  Not found — creating..."
echo ""

# POST the config; Coveo returns the created source's id
echo "POSTing source config..."
http_code=$(
  curl -sS -o /tmp/_src_resp.json -w "%{http_code}" -X POST \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    "${SOURCES_URL}?rebuild=false" \
    --data-binary @"$CONFIG_FILE"
)

if [[ ! "$http_code" =~ ^20[0-9]$ ]]; then
  echo "  ✗ POST failed (HTTP $http_code):" >&2
  cat /tmp/_src_resp.json >&2
  echo "" >&2
  rm -f /tmp/_src_resp.json
  exit 1
fi

new_id=$(python3 -c "import json; print(json.load(open('/tmp/_src_resp.json')).get('id',''))")
rm -f /tmp/_src_resp.json

if [[ -z "$new_id" ]]; then
  echo "  ✗ Could not read source id from response" >&2
  exit 1
fi

echo "  ✓ Source created: $new_id"

# Append to .env if not already there
if ! grep -q "^COVEO_SITEMAP_SOURCE_ID=" "$ENV_FILE"; then
  echo "COVEO_SITEMAP_SOURCE_ID=$new_id" >> "$ENV_FILE"
  echo "  Wrote COVEO_SITEMAP_SOURCE_ID to .env"
else
  echo "  ⚠️  .env already has COVEO_SITEMAP_SOURCE_ID — leaving it untouched. Update manually if needed."
fi
