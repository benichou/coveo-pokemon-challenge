#!/usr/bin/env bash
#
# Validate that the Coveo org has the licensed features this project needs.
#
# Checks the org license endpoint and reports whether the following are
# enabled:
#   - Passage Retrieval API (Bonus tier)
#   - Relevance Generative Answering / CRGA (Advanced tier RGA)
#   - Automatic Relevance Tuning (used implicitly by ML ranking)
#
# These were activated by Coveo via email on 2026-05-29 (Will Tseng). This
# script re-verifies that they're still on whenever you run it — useful as a
# pre-demo check or after any org-level change.
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY   (Organization: View is sufficient; admin works too)
#
# Exit code: 0 if all required features are enabled, 1 if any is disabled.

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
: "${COVEO_ADMIN_API_KEY:?missing in .env}"

LICENSE_URL="https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/license"

echo "Fetching org license for ${COVEO_ORG_ID}..."
http_code=$(
  curl -sS -o /tmp/_license.json -w "%{http_code}" \
    -H "Authorization: Bearer ${COVEO_ADMIN_API_KEY}" \
    "$LICENSE_URL"
)

if [[ "$http_code" != "200" ]]; then
  echo "  ✗ License fetch failed (HTTP $http_code):" >&2
  cat /tmp/_license.json >&2
  echo "" >&2
  rm -f /tmp/_license.json
  exit 1
fi
echo "  ✓ License retrieved."
echo ""

python3 - <<'PY'
import json, sys

with open('/tmp/_license.json') as f:
    d = json.load(f)

# The features this project depends on. Path is documented inline so
# future-you can find them in the license response if Coveo restructures.
checks = [
    ("Passage Retrieval",            ['machineLearningModels', 'passageRetrieval', 'enabled']),
    ("Relevance Generative Answer",  ['machineLearningModels', 'relevanceGenerativeAnswering', 'enabled']),
    ("Automatic Relevance Tuning",   ['machineLearningModels', 'automaticRelevanceTuning', 'enabled']),
]

def get_path(obj, path):
    for k in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    return obj

all_ok = True
for name, path in checks:
    enabled = get_path(d, path)
    if enabled is True:
        print(f"  ✓ {name}: enabled")
    else:
        print(f"  ✗ {name}: {'disabled' if enabled is False else 'unknown'}")
        all_ok = False

# Bonus info: surface model count limits so we know what we can build
print()
print("Capacity limits:")
for name, path_prefix in [
    ("Passage Retrieval",           ['machineLearningModels', 'passageRetrieval']),
    ("Relevance Generative Answer", ['machineLearningModels', 'relevanceGenerativeAnswering']),
]:
    info = get_path(d, path_prefix) or {}
    limit = info.get('numberOfModelsLimit')
    if limit is not None:
        print(f"  · {name}: up to {limit} models")

sys.exit(0 if all_ok else 1)
PY

result=$?
rm -f /tmp/_license.json

if [[ $result -eq 0 ]]; then
  echo ""
  echo "All required features are enabled. ✓"
else
  echo ""
  echo "One or more required features are NOT enabled. ✗" >&2
  echo "If the org should have these, contact Coveo to enable them." >&2
  exit 1
fi
