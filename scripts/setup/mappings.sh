#!/usr/bin/env bash
#
# Add field mappings to a Coveo source. Picks which source + which field list
# based on the single argument:
#
#   scripts/setup/mappings.sh sitemap   ← the 5 Source A fields
#   scripts/setup/mappings.sh push      ← the 5 Source A fields + 8 Source B enrichments
#
# Why this exists: when this project was built (May 2026), the Coveo Admin
# Console didn't expose a mappings UI for the new Sitemap source. The REST API
# does, so we manage source mappings programmatically. The Push source also
# needs mappings because Coveo's Push API stores submitted JSON fields as
# document metadata — those metadata values still need a mapping rule to land
# in the search-time indexed fields.
#
# Each mapping links a metadata key (e.g. `pokemon_type`) to its same-named
# indexed field via the `%[pokemon_type]` placeholder.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID              Coveo organization ID
#   COVEO_ADMIN_API_KEY       Key with Content > Sources > Edit privilege
#   COVEO_SITEMAP_SOURCE_ID   (when called with `sitemap`)
#   COVEO_PUSH_SOURCE_ID      (when called with `push`)
#
# Idempotent: lists existing common mappings first and skips any field that
# already has a rule, so re-running is safe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

usage() {
  cat <<EOF
Usage: $0 <kind>

  kind:
    sitemap   Map the 5 scraping-config fields to the pokemondb-sitemap source.
    push      Map all 13 fields (5 base + 8 enrichments) to the pokemondb-push source.

After running, trigger a rebuild on the source for the change to take effect:
    scripts/source/rebuild.sh                  # sitemap (existing)
    # Push source applies mappings on the next document push.
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

KIND="$1"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env (needs Content > Sources > Edit)}"

case "$KIND" in
  sitemap)
    : "${COVEO_SITEMAP_SOURCE_ID:?missing in .env}"
    SOURCE_ID="$COVEO_SITEMAP_SOURCE_ID"
    SOURCE_LABEL="pokemondb-sitemap"
    FIELDS=(pokemon_name pokemon_type image_url dex_number generation)
    ;;
  push)
    : "${COVEO_PUSH_SOURCE_ID:?missing in .env}"
    SOURCE_ID="$COVEO_PUSH_SOURCE_ID"
    SOURCE_LABEL="pokemondb-push"
    # Source B uses all 5 base fields + 8 PokéAPI enrichment fields.
    FIELDS=(
      pokemon_name
      pokemon_type
      image_url
      dex_number
      generation
      base_hp
      base_attack
      base_defense
      base_sp_attack
      base_sp_defense
      base_speed
      abilities
      is_form_variant
      base_species
    )
    ;;
  *)
    echo "ERROR: unknown kind '$KIND'" >&2
    usage >&2
    exit 1
    ;;
esac

API_BASE="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${SOURCE_ID}/mappings"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

echo "Source: $SOURCE_LABEL (id=$SOURCE_ID)"
echo "Fields to map: ${#FIELDS[@]}"
echo ""

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
if [[ "$KIND" == "sitemap" && $created -gt 0 ]]; then
  echo "Trigger a source rebuild for changes to apply to existing indexed items:"
  echo "  scripts/source/rebuild.sh"
fi
