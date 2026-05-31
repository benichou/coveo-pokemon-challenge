#!/usr/bin/env bash
#
# Apply the web scraping configuration stored at config/source/scraping.json
# to the pokemondb-sitemap source via the Coveo REST API.
#
# The scraping config is what tells Coveo how to extract metadata from each
# crawled Pokemon page (CSS / XPath selectors for name, type, image, etc.).
# Keeping it as a versioned JSON file lets us:
#   - Diff and review selector changes in git history
#   - Reproduce the org's scraping setup from scratch
#   - Roll back to a known-good version
#
# Coveo stores this as a JSON STRING inside the source's scrapingConfiguration
# field, so we read the human-readable JSON file, stringify (compact) it, and
# write it back via PUT /sources/{id}.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_SITEMAP_SOURCE_ID
#   COVEO_ADMIN_API_KEY    (needs Content > Sources > Edit)
#
# Usage:
#   scripts/update_scraping_config.sh
#
# After running, trigger a rebuild for changes to apply to indexed items:
#   scripts/rebuild_source.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
CONFIG_FILE="$REPO_ROOT/config/source/scraping.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "ERROR: scraping config not found at $CONFIG_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_SITEMAP_SOURCE_ID:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env}"

API_BASE="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${COVEO_SITEMAP_SOURCE_ID}"
AUTH_HEADER="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"

echo "Validating local config..."
python3 - <<PY
import json, sys
try:
    cfg = json.load(open("$CONFIG_FILE"))
except json.JSONDecodeError as e:
    print(f"  ✗ scraping_config.json is not valid JSON: {e}", file=sys.stderr)
    sys.exit(1)
if not isinstance(cfg, list):
    print("  ✗ scraping_config.json must be a JSON array of configurations", file=sys.stderr)
    sys.exit(1)
names = [c.get("name", "(unnamed)") for c in cfg]
print(f"  ✓ {len(cfg)} configurations: {names}")
PY

echo ""
echo "Fetching current source state..."
curl -sS -H "$AUTH_HEADER" "$API_BASE" -o /tmp/_src.json
echo "  ✓ Got current source."

echo ""
echo "Building updated source payload..."
CONFIG_FILE="$CONFIG_FILE" python3 - > /tmp/_src_patched.json <<'PY'
import json, os

with open('/tmp/_src.json') as f:
    src = json.load(f)
with open(os.environ['CONFIG_FILE']) as f:
    new_scraping = json.load(f)

# Coveo stores the scraping config as a JSON STRING blob inside the source.
src['scrapingConfiguration'] = json.dumps(new_scraping, separators=(',', ':'), ensure_ascii=False)

# Drop server-managed fields before PUT
for k in ('information', 'resourceId', 'owner', 'lastModifier',
          'lastModifiedDate', 'createdDate'):
    src.pop(k, None)

print(json.dumps(src))
PY
echo "  ✓ Payload built."

echo ""
echo "PUT updated source..."
http_code=$(
  curl -sS -o /tmp/_put_resp.json -w "%{http_code}" -X PUT \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    "$API_BASE" \
    --data-binary @/tmp/_src_patched.json
)

if [[ "$http_code" != "200" && "$http_code" != "204" ]]; then
  echo "  ✗ PUT failed (HTTP $http_code):" >&2
  cat /tmp/_put_resp.json >&2
  echo "" >&2
  rm -f /tmp/_src.json /tmp/_src_patched.json /tmp/_put_resp.json
  exit 1
fi
echo "  ✓ Source updated (HTTP $http_code)."
rm -f /tmp/_src.json /tmp/_src_patched.json /tmp/_put_resp.json
echo ""
echo "Scraping configuration applied from $CONFIG_FILE"
echo "Next: trigger a rebuild → scripts/rebuild_source.sh"
