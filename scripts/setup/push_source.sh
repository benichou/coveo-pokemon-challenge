#!/usr/bin/env bash
#
# Create the Push source defined in config/source_push/definition.json.
# Idempotent: if a source with the same name already exists, skip and write
# its ID to .env (so the Python push pipeline can find it).
#
# Source B (Push) hosts form variants of Pokemon (Mega Charizard X/Y, Hisuian
# Decidueye, Galarian Zigzagoon, etc.) — content that Source A (Sitemap)
# structurally can't capture because pokemondb.net uses one URL per base
# species. The Python pipeline in push-pokemon/ pulls these from PokéAPI
# and pushes them via the Coveo Push API into this source.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY   (needs Content > Sources > Edit)
#
# Usage:
#   scripts/setup/push_source.sh
#
# On success, prints the source ID and (if not already there) writes
# COVEO_PUSH_SOURCE_ID=<id> to ../.env.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
CONFIG_FILE="$REPO_ROOT/config/source_push/definition.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: Push source config not found at $CONFIG_FILE" >&2
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
  echo "  ✓ Push source already exists: $existing_id"
  if ! grep -q "^COVEO_PUSH_SOURCE_ID=$existing_id" "$ENV_FILE" 2>/dev/null; then
    if grep -q "^COVEO_PUSH_SOURCE_ID=" "$ENV_FILE"; then
      # Has an empty or different value — replace it
      python3 - "$ENV_FILE" "$existing_id" <<'PY'
import sys
env_path, new_id = sys.argv[1], sys.argv[2]
lines = open(env_path).readlines()
with open(env_path, "w") as f:
    for line in lines:
        if line.startswith("COVEO_PUSH_SOURCE_ID="):
            f.write(f"COVEO_PUSH_SOURCE_ID={new_id}\n")
        else:
            f.write(line)
PY
      echo "  Updated COVEO_PUSH_SOURCE_ID in .env"
    else
      echo "COVEO_PUSH_SOURCE_ID=$existing_id" >> "$ENV_FILE"
      echo "  Wrote COVEO_PUSH_SOURCE_ID to .env"
    fi
  fi
  exit 0
fi

echo "  Not found — creating..."
echo ""

echo "POSTing Push source config..."
http_code=$(
  curl -sS -o /tmp/_src_push_resp.json -w "%{http_code}" -X POST \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    "${SOURCES_URL}?rebuild=false" \
    --data-binary @"$CONFIG_FILE"
)

if [[ ! "$http_code" =~ ^20[0-9]$ ]]; then
  echo "  ✗ POST failed (HTTP $http_code):" >&2
  cat /tmp/_src_push_resp.json >&2
  echo "" >&2
  rm -f /tmp/_src_push_resp.json
  exit 1
fi

new_id=$(python3 -c "import json; print(json.load(open('/tmp/_src_push_resp.json')).get('id',''))")
rm -f /tmp/_src_push_resp.json

if [[ -z "$new_id" ]]; then
  echo "  ✗ Could not read source id from response" >&2
  exit 1
fi

echo "  ✓ Push source created: $new_id"

if grep -q "^COVEO_PUSH_SOURCE_ID=" "$ENV_FILE"; then
  # Replace existing (possibly empty) value
  python3 - "$ENV_FILE" "$new_id" <<'PY'
import sys
env_path, new_id = sys.argv[1], sys.argv[2]
lines = open(env_path).readlines()
with open(env_path, "w") as f:
    for line in lines:
        if line.startswith("COVEO_PUSH_SOURCE_ID="):
            f.write(f"COVEO_PUSH_SOURCE_ID={new_id}\n")
        else:
            f.write(line)
PY
  echo "  Updated COVEO_PUSH_SOURCE_ID in .env"
else
  echo "COVEO_PUSH_SOURCE_ID=$new_id" >> "$ENV_FILE"
  echo "  Wrote COVEO_PUSH_SOURCE_ID to .env"
fi
