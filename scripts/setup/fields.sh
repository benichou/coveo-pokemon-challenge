#!/usr/bin/env bash
#
# Create the Coveo fields defined in config/fields.json. Idempotent: skips any
# field that already exists (matched by name).
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY   (needs Content > Fields > Edit)
#
# Usage:
#   scripts/create_fields.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
CONFIG_FILE="$REPO_ROOT/config/fields.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: fields config not found at $CONFIG_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env (needs Content > Fields > Edit)}"

FIELDS_URL="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/indexes/fields"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

echo "Reading desired field definitions..."
desired_names=$(python3 -c "
import json
for f in json.load(open('$CONFIG_FILE')):
    print(f['name'])
")
desired_count=$(echo "$desired_names" | grep -c .)
echo "  $desired_count fields declared in $CONFIG_FILE"
echo ""

echo "Fetching existing fields..."
existing_names=$(
  curl -sS -H "$AUTH_HEADER" "https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/indexes/page/fields?page=0&perPage=200&origin=USER" \
    | python3 -c "
import json, sys
d = json.load(sys.stdin)
items = d.get('items', d) if isinstance(d, dict) else d
for f in items:
    print(f['name'])
"
)
echo "  $(echo "$existing_names" | grep -c .) existing user fields on the org."
echo ""

created=0
skipped=0

while IFS= read -r field_name; do
  [[ -z "$field_name" ]] && continue

  if echo "$existing_names" | grep -qx "$field_name"; then
    printf "  [skip]    %s — already exists\n" "$field_name"
    skipped=$((skipped + 1))
    continue
  fi

  # Extract just this field's definition and POST it as a single-item array,
  # which is what Coveo's batch endpoint expects.
  payload=$(CONFIG_FILE="$CONFIG_FILE" FIELD_NAME="$field_name" python3 - <<'PY'
import json, os
with open(os.environ['CONFIG_FILE']) as f:
    fields = json.load(f)
target = next(f for f in fields if f['name'] == os.environ['FIELD_NAME'])
print(json.dumps([target]))
PY
)

  printf "  [create]  %s ... " "$field_name"
  http_code=$(
    curl -sS -o /tmp/_fld_resp.json -w "%{http_code}" -X POST \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json" \
      "${FIELDS_URL}/batch/create" \
      -d "$payload"
  )

  if [[ "$http_code" =~ ^20[0-9]$ ]]; then
    echo "HTTP $http_code ✓"
    created=$((created + 1))
  else
    echo "HTTP $http_code ✗"
    cat /tmp/_fld_resp.json >&2
    echo "" >&2
    rm -f /tmp/_fld_resp.json
    exit 1
  fi
  rm -f /tmp/_fld_resp.json
done <<< "$desired_names"

echo ""
echo "Done: $created created, $skipped skipped (already existed)."
