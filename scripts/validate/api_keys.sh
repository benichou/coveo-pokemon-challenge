#!/usr/bin/env bash
#
# Validate that the three project API keys are functional and have the right
# privileges:
#
#   COVEO_PUSH_API_KEY    — Push API key (Push template). Should have:
#                             - Sources: View all
#                             - Push items to sources
#                           Test: GET /sources should succeed (200).
#                                 POST a mapping should fail with 403 (no Edit).
#
#   COVEO_ADMIN_API_KEY   — Source admin key (Custom template). Should have:
#                             - Sources: Edit (on All)
#                             - Fields: Edit (on All)
#                           Test: GET /sources/{id}/mappings succeeds (200).
#                                 POST an empty body mapping returns 4xx body-
#                                 validation error (NOT 401/403), proving auth
#                                 + Edit privilege are in place.
#
#   COVEO_SEARCH_API_KEY  — Anonymous Search key (template), bound to the
#                           pokemon-search search hub. Should have:
#                             - Execute queries: Allowed
#                             - Analytics data: Push
#                             - NO Sources: Edit
#                           Test: POST /search/v2 succeeds (200).
#                                 POST a mapping fails with 403.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_SITEMAP_SOURCE_ID
#   COVEO_PUSH_API_KEY
#   COVEO_ADMIN_API_KEY
#   COVEO_SEARCH_API_KEY
#
# Exit code: 0 if all three keys work as expected, 1 otherwise.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
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
: "${COVEO_PUSH_API_KEY:?missing in .env}"
: "${COVEO_ADMIN_API_KEY:?missing in .env}"
: "${COVEO_SEARCH_API_KEY:?missing in .env}"

API_BASE="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}"
SOURCES_URL="${API_BASE}/sources"
MAPPINGS_URL="${API_BASE}/sources/${COVEO_SITEMAP_SOURCE_ID}/mappings"
RULES_URL="${MAPPINGS_URL}/common/rules"

failures=0

check() {
  # check <name> <expected_pass_codes> <actual_code> [<extra_msg>]
  local name=$1
  local expected=$2
  local actual=$3
  local extra=${4:-}
  if [[ ",${expected}," == *",${actual},"* ]]; then
    printf "  ✓ %-58s (HTTP %s)\n" "$name" "$actual"
  else
    printf "  ✗ %-58s (HTTP %s) %s\n" "$name" "$actual" "$extra"
    failures=$((failures + 1))
  fi
}

echo "Validating COVEO_PUSH_API_KEY (push template)..."

# Test 1: Push key can read sources (Sources: View)
code=$(curl -sS -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${COVEO_PUSH_API_KEY}" \
  "$SOURCES_URL")
check "Push key authenticates + Sources: View (GET /sources)" "200" "$code"

# Test 2: Push key should NOT have Sources: Edit
# POST a minimal valid-but-meaningless payload; expect 403, not 201
code=$(curl -sS -o /tmp/_probe.json -w "%{http_code}" -X POST \
  -H "Authorization: Bearer ${COVEO_PUSH_API_KEY}" \
  -H "Content-Type: application/json" \
  "$RULES_URL" \
  -d '{"field":"_validation_probe","content":["%[_x]"]}')
rm -f /tmp/_probe.json
check "Push key correctly DENIED Sources: Edit (POST mapping)" "403" "$code" "expected 403 (push key shouldn't have Edit)"

echo ""
echo "Validating COVEO_ADMIN_API_KEY (custom template, source admin)..."

# Test 3: Admin key can read mappings (Sources: View — implicit in Edit)
code=$(curl -sS -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${COVEO_ADMIN_API_KEY}" \
  "$MAPPINGS_URL")
check "Admin key authenticates + Sources: View (GET /mappings)" "200" "$code"

# Test 4: Admin key has Sources: Edit
# POST an empty body — expect a 4xx body-validation error (400/412), NOT 401/403
code=$(curl -sS -o /tmp/_probe.json -w "%{http_code}" -X POST \
  -H "Authorization: Bearer ${COVEO_ADMIN_API_KEY}" \
  -H "Content-Type: application/json" \
  "$RULES_URL" \
  -d '{}')
rm -f /tmp/_probe.json
# Accept 400 (invalid json) or 412 (precondition failed = missing param) as
# proof that auth+privilege succeeded and only the empty body was rejected.
check "Admin key has Sources: Edit (POST gets body error, not auth error)" "400,412" "$code" "expected 400/412; got auth failure if 401/403"

echo ""
echo "Validating COVEO_SEARCH_API_KEY (anonymous search template, bound to pokemon-search hub)..."

SEARCH_URL="${API_BASE}/../../search/v2?organizationId=${COVEO_ORG_ID}"
# Use the cleaner search endpoint (not under /organizations)
SEARCH_URL="https://platform.cloud.coveo.com/rest/search/v2?organizationId=${COVEO_ORG_ID}"

# Test 5: Search key can execute a query (Execute queries: Allowed)
code=$(curl -sS -o /dev/null -w "%{http_code}" -X POST \
  -H "Authorization: Bearer ${COVEO_SEARCH_API_KEY}" \
  -H "Content-Type: application/json" \
  "$SEARCH_URL" \
  -d '{"q":"","searchHub":"pokemon-search","numberOfResults":1}')
check "Search key can execute queries (POST /search/v2)" "200" "$code" "expected 200 (search key needs Execute queries privilege)"

# Test 6: Search key should NOT have Sources: Edit
code=$(curl -sS -o /tmp/_probe.json -w "%{http_code}" -X POST \
  -H "Authorization: Bearer ${COVEO_SEARCH_API_KEY}" \
  -H "Content-Type: application/json" \
  "$RULES_URL" \
  -d '{"field":"_validation_probe","content":["%[_x]"]}')
rm -f /tmp/_probe.json
check "Search key correctly DENIED Sources: Edit (POST mapping)" "403" "$code" "expected 403 (search key shouldn't have Edit)"

echo ""
if [[ $failures -eq 0 ]]; then
  echo "All three API keys validated. ✓"
  exit 0
else
  echo "$failures check(s) failed. ✗" >&2
  exit 1
fi
