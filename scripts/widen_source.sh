#!/usr/bin/env bash
#
# Update the pokemondb-sitemap source's URL inclusion filter (and optionally
# add the standard exclusion rules) to one of three preset scopes. Used to
# stage the crawl: 1 Pokemon → 8 diverse Pokemon → all Pokemon.
#
# Why this is scripted: changing the URL filter in the Admin Console is a
# few clicks but we make this transition twice (spot-check, then full).
# Scripting it makes both transitions one-line and idempotent, and gives the
# Topic 1 panel a "config as code" story.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_SITEMAP_SOURCE_ID
#   COVEO_ADMIN_API_KEY    (needs Content > Sources > Edit)
#
# Usage:
#   scripts/widen_source.sh narrow       # only bulbasaur
#   scripts/widen_source.sh spot-check   # 8 diverse Pokemon (edge-case sweep)
#   scripts/widen_source.sh all          # all ~1,025 Pokemon + exclusions
#
# After running this you still need to trigger a rebuild:
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
: "${COVEO_ADMIN_API_KEY:?missing in .env}"

usage() {
  cat <<EOF
Usage: $0 <mode>

Modes:
  narrow       Only the bulbasaur page (fast iteration)
  spot-check   8 diverse Pokemon (catches selector edge cases)
  all          All ~1,025 Pokemon + 9 exclusion rules (production)

After running, trigger a rebuild:
  scripts/rebuild_source.sh
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

MODE=$1

# Build the inclusion regex based on the mode. Each is an anchored regex
# (^...$) for tightness, so /pokedex/all and /pokedex/national etc. don't
# slip through.
case "$MODE" in
  narrow)
    INCLUDE_REGEX='^https://pokemondb\.net/pokedex/bulbasaur$'
    ADD_EXCLUSIONS=false
    DESCRIPTION='1 Pokemon (Bulbasaur)'
    ;;
  spot-check)
    # Diverse picks covering: multiple generations, hyphenated names,
    # single- and dual-type, mid- and end-stage evolutions, legendary.
    INCLUDE_REGEX='^https://pokemondb\.net/pokedex/(bulbasaur|pikachu|charizard|mewtwo|ho-oh|mr-mime|decidueye|miraidon)$'
    ADD_EXCLUSIONS=false
    DESCRIPTION='8 diverse Pokemon (edge-case sweep)'
    ;;
  all)
    INCLUDE_REGEX='^https://pokemondb\.net/pokedex/[a-z0-9-]+$'
    ADD_EXCLUSIONS=true
    DESCRIPTION='all ~1,025 Pokemon (production)'
    ;;
  *)
    echo "ERROR: unknown mode '$MODE'" >&2
    usage >&2
    exit 1
    ;;
esac

API_BASE="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${COVEO_SITEMAP_SOURCE_ID}"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

echo "Mode: $MODE  →  $DESCRIPTION"
echo "Include regex: $INCLUDE_REGEX"
echo "Apply exclusions: $ADD_EXCLUSIONS"
echo ""

# Step 1: GET current source config
echo "Fetching current source config..."
curl -sS -H "$AUTH_HEADER" "$API_BASE" -o /tmp/_source.json
echo "  ✓ Got current source."

# Step 2: Build the new urlFilters list with python, preserving the rest of
# the source object as-is. Regex and flag passed via env to avoid bash/python
# string-escape collisions.
INCLUDE_REGEX="$INCLUDE_REGEX" ADD_EXCLUSIONS="$ADD_EXCLUSIONS" python3 - > /tmp/_source_patched.json <<'PY'
import json, os

with open('/tmp/_source.json') as f:
    src = json.load(f)

include_regex = os.environ['INCLUDE_REGEX']
add_exclusions = os.environ['ADD_EXCLUSIONS'] == 'true'

# Inclusion filter (single, replaces any previous one)
new_filters = [
    {
        "filter": include_regex,
        "filterType": "REGEX",
        "includeFilter": True,
    }
]

if add_exclusions:
    exclusion_substrings = [
        "/move/",
        "/type/",
        "/ability/",
        "/item/",
        "/location/",
        "/pokedex/stats/",
        "/pokedex/national",
        "/pokedex/all",
        "/pokedex/game/",
    ]
    for sub in exclusion_substrings:
        new_filters.append({
            "filter": f"*{sub}*",
            "filterType": "WILDCARD",
            "includeFilter": False,
        })

src["urlFilters"] = new_filters

# Drop server-managed fields that shouldn't go back on PUT
for k in ("information", "resourceId", "owner", "lastModifier",
          "lastModifiedDate", "createdDate"):
    src.pop(k, None)

print(json.dumps(src))
PY

# Step 3: PUT the updated source back. Use the plain /sources/{id} endpoint
# which accepts the full source object directly (no envelope).
echo "Submitting updated source config..."
http_code=$(
  curl -sS -o /tmp/_put_resp.json -w "%{http_code}" -X PUT \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    "$API_BASE" \
    --data-binary @/tmp/_source_patched.json
)

if [[ "$http_code" != "200" && "$http_code" != "204" ]]; then
  echo "  ✗ PUT failed (HTTP $http_code):" >&2
  cat /tmp/_put_resp.json >&2
  echo "" >&2
  rm -f /tmp/_source.json /tmp/_source_patched.json /tmp/_put_resp.json
  exit 1
fi

echo "  ✓ Source updated (HTTP $http_code)."
rm -f /tmp/_source.json /tmp/_source_patched.json /tmp/_put_resp.json
echo ""
echo "URL filters set for mode: $MODE"
echo "Next: trigger a rebuild → scripts/rebuild_source.sh"
