#!/usr/bin/env bash
#
# Add the 5 Pokemon Challenge field mappings to the Coveo Sitemap source.
#
# Why this exists: when this project was built (May 2026), the Coveo Admin
# Console didn't expose a mappings UI for the new Sitemap source. The REST API
# does, so we manage source mappings programmatically.
#
# Each mapping links a scraping-config metadata key (e.g. `pokemon_type` from
# the web scraping config) to its same-named indexed field (`@pokemon_type`),
# so the extracted value lands somewhere search and facets can use.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID                Coveo organization ID
#   COVEO_SITEMAP_SOURCE_ID     ID of the pokemondb-sitemap source
#   COVEO_ADMIN_API_KEY         Key with Content > Sources > Edit privilege
#
# Idempotent: lists existing common mappings first and skips any field that
# already has a rule, so re-running is safe.
#
# Usage:
#   scripts/add_mappings.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi

# Load .env into the environment
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_SITEMAP_SOURCE_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env (needs Content > Sources > Edit)}"

API_BASE="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${COVEO_SITEMAP_SOURCE_ID}/mappings"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

# The 5 Pokemon Challenge fields. Each gets a single rule mapping
# %[field_name] (metadata key from the web scraping config) → @field_name.
FIELDS=(
  pokemon_name
  pokemon_type
  image_url
  dex_number
  generation
)

echo "Fetching existing common mappings..."
existing=$(
  curl -sS -H "$AUTH_HEADER" "$API_BASE" \
    | python3 -c "
import json, sys
d = json.load(sys.stdin)
for r in d.get('common', {}).get('rules', []):
    f = r.get('field')
    if f:
        print(f)
"
)
existing_count=$(echo "$existing" | grep -c . || true)
echo "  $existing_count existing common mappings on this source."
echo ""

created=0
skipped=0

for field in "${FIELDS[@]}"; do
  if echo "$existing" | grep -qx "$field"; then
    echo "  [skip]    $field — already mapped"
    skipped=$((skipped + 1))
    continue
  fi

  printf "  [create]  %s ... " "$field"
  http_code=$(
    curl -sS -o /tmp/_map_resp.json -w "%{http_code}" -X POST \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json" \
      "${API_BASE}/common/rules" \
      -d "{\"field\":\"${field}\",\"content\":[\"%[${field}]\"]}"
  )

  if [[ "$http_code" == "201" ]]; then
    echo "HTTP 201 ✓"
    created=$((created + 1))
  else
    echo "HTTP $http_code ✗"
    cat /tmp/_map_resp.json >&2
    echo "" >&2
    rm -f /tmp/_map_resp.json
    exit 1
  fi
  rm -f /tmp/_map_resp.json
done

echo ""
echo "Done: $created created, $skipped skipped."
echo "Trigger a source rebuild for changes to apply to indexed items."
