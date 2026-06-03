#!/usr/bin/env bash
#
# scripts/ml/seed_query_suggest.sh — upload a Default Queries file to the
# pokemon-qs Coveo QS model via the documented Advanced Model Configurations
# API. The next QS model rebuild incorporates the queries as suggestion
# candidates immediately (Coveo's official preload path; no need to wait
# for organic UA engagement signals to accumulate).
#
# Why this approach (after a long spike)
# --------------------------------------
# We tried two wrong paths before finding this one:
#
#   1. Writing to extraConfig.defaultQueries on the QS model. Coveo
#      accepted the PUT and the JSON editor in the Console showed the
#      data persisted, but the QS engine never read it (the field is
#      actually a Drill-engine parameter — Coveo doesn't validate that
#      an extraConfig field applies to the model's engine). modelSize
#      stayed at 5 across multiple rebuilds.
#
#   2. UA synthesis — POSTing 456 synthetic search events (and later
#      another 456 with click chains) to /rest/ua/v15/analytics/search.
#      Events flowed through the ingestion pipeline (searchEventCount
#      grew correctly) but never became candidates: Coveo's QS algorithm
#      explicitly requires "queries performed and followed by at least
#      one click on search results" before promotion, and our synthetic
#      click events were filtered out (clickEventCount stayed at 47).
#
# The documented preload path is what Coveo's own docs call a "Default
# Queries file" — a UTF-8 CSV with two columns (query, importance) PUT to
# /machinelearning/models/{id}/configs/DEFAULT_QUERIES?languageCode=en
# as multipart/form-data with field name `configFile`. The next rebuild
# incorporates the file's contents as candidates directly (no UA event
# detour, no click-rate threshold).
#
# Required env (../../.env):
#   COVEO_ORG_ID
#   COVEO_ML_MODELS_API_KEY   needs: Machine Learning > Models > Edit
#
# Usage:
#   scripts/ml/seed_query_suggest.sh             # apply
#   scripts/ml/seed_query_suggest.sh --dry-run   # show plan + CSV preview
#
# Re-runnable: each PUT replaces the existing Default Queries file
# entirely (Coveo's API semantics — the request is idempotent).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
QUERIES_FILE="$REPO_ROOT/config/ml/default-queries.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$QUERIES_FILE" ]]; then
  echo "ERROR: queries file not found at $QUERIES_FILE" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${COVEO_ORG_ID:?missing in .env}"
: "${COVEO_ML_MODELS_API_KEY:?missing in .env}"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

MODEL_NAME="pokemon-qs"
LANGUAGE_CODE="en"

# ---------------------------------------------------------------------------
# Step 1: discover the pokemon-qs model ID by display name.
# ---------------------------------------------------------------------------
echo "[1/3] Looking up '$MODEL_NAME' model ID..."
models_resp=$(/usr/bin/curl -sS -H "Authorization: Bearer $COVEO_ML_MODELS_API_KEY" \
  "https://platform.cloud.coveo.com/rest/organizations/$COVEO_ORG_ID/machinelearning/models")
MODEL_ID=$(echo "$models_resp" | MODEL_NAME="$MODEL_NAME" python3 -c "
import json, os, sys
models = json.load(sys.stdin)
m = next((m for m in models if m.get('modelDisplayName') == os.environ['MODEL_NAME']), None)
if not m:
    print(f\"ERROR: no model with displayName '{os.environ['MODEL_NAME']}'\", file=sys.stderr)
    sys.exit(1)
print(m['id'])
")
echo "  ✓ $MODEL_NAME → $MODEL_ID"

# ---------------------------------------------------------------------------
# Step 2: regenerate the CSV from default-queries.json. Two columns: query,weight.
#
# Importance weighting:
#   - Pokemon names get weight 10 (primary use case — most searches are name
#     lookups on a Pokédex)
#   - Type/generation filters get 5 (medium-frequency)
#   - Natural-language questions get 3 (least common typing pattern)
#
# The weight is an integer that represents the relative importance of each
# query; Coveo's QS algorithm uses it as if it were a past occurrence count
# from real UA. If no weight is given, all queries are treated equally.
#
# The CSV is written to a VERSIONED path in the repo (not /tmp) so it lives
# alongside the JSON as a Coveo-uploaded artifact. The JSON is the human-
# authored source; the CSV is the generated payload that Coveo actually
# receives. Both get committed so diffs of one match diffs of the other.
# ---------------------------------------------------------------------------
CSV_FILE="$REPO_ROOT/config/ml/default-queries.csv"
python3 <<PYEOF > "$CSV_FILE"
import json
data = json.load(open("$QUERIES_FILE"))
# Header comment — Coveo's CSV parser treats lines starting with # as data,
# so we can't actually include a header. The file's purpose is documented
# in docs/ml-models.md and config/ml/default-queries.json instead.
for q in data.get("names", []):
    print(f"{q},10")
for q in data.get("type_and_generation", []):
    print(f"{q},5")
for q in data.get("natural_language_questions", []):
    print(f"{q},3")
PYEOF
NUM_ROWS=$(wc -l < "$CSV_FILE" | tr -d ' ')
echo ""
echo "[2/3] Regenerated $CSV_FILE with $NUM_ROWS rows (weighted by category)."
echo "      Sample:"
head -3 "$CSV_FILE" | sed 's/^/        /'
echo "        ..."
tail -3 "$CSV_FILE" | sed 's/^/        /'
echo ""
echo "      Tip: commit both default-queries.json AND default-queries.csv —"
echo "      the JSON is the source of truth; the CSV is the artifact Coveo receives."

if $DRY_RUN; then
  echo ""
  echo "Dry run complete. CSV regenerated at $CSV_FILE. No upload performed."
  exit 0
fi

# ---------------------------------------------------------------------------
# Step 3: upload via PUT to /configs/DEFAULT_QUERIES.
# ---------------------------------------------------------------------------
URL="https://platform.cloud.coveo.com/rest/organizations/$COVEO_ORG_ID/machinelearning/models/$MODEL_ID/configs/DEFAULT_QUERIES?languageCode=$LANGUAGE_CODE"
echo ""
echo "[3/3] PUT $URL"
upload_resp=$(/usr/bin/curl -sS -w "\n%{http_code}" -X PUT \
  -H "Authorization: Bearer $COVEO_ML_MODELS_API_KEY" \
  -F "configFile=@$CSV_FILE;type=text/csv" \
  "$URL")
upload_body=$(echo "$upload_resp" | sed '$d')
upload_code=$(echo "$upload_resp" | tail -n1)

if [[ "$upload_code" =~ ^2 ]]; then
  echo "  ✓ Default Queries file uploaded (HTTP $upload_code)."
  echo "  Response: $upload_body"
  echo ""
  echo "Done. The next QS model rebuild will incorporate these queries as"
  echo "candidates. Trigger a rebuild via Console (Configuration → Save) or"
  echo "wait for the next daily auto-rebuild (~01:47 UTC)."
else
  echo "  ✗ Upload failed (HTTP $upload_code):" >&2
  echo "$upload_body" | head -10 >&2
  exit 1
fi
