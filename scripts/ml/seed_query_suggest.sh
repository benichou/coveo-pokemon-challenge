#!/usr/bin/env bash
#
# scripts/ml/seed_query_suggest.sh — preload the pokemon-qs Query Suggest model
# with a curated list of starter queries from config/ml/default-queries.json.
#
# Why this exists
# ---------------
# A freshly-built QS model has no organic UA history to learn from (we'd need
# weeks of real traffic before Coveo's algorithm sees enough events). To make
# type-ahead useful on day one — and to give the panel demo real suggestions
# the moment they click into the search box — we preload a curated list of
# Pokémon-flavored queries. Over time, real UA events from the live site
# accumulate alongside the seed; Coveo's QS model blends both at training.
#
# Why script it
#   - Reproducibility: re-run on a fresh org (or after a model rebuild) and
#     the same seed list is uploaded.
#   - Versioning: config/ml/default-queries.json is the single source of truth
#     for what we preload. Diff the file → see what changed → re-run the script.
#   - Idempotency: a re-run with the same payload is a no-op from the user's
#     perspective (Coveo accepts the PUT either way).
#
# What it does
#   1. Reads config/ml/default-queries.json and flattens names + types + Qs
#      into a single deduped query list.
#   2. Looks up the pokemon-qs model ID by display name.
#   3. PUTs the seed list onto the model via the Advanced Model Configurations
#      API.
#   4. Prints the response so any rejection (wrong field name, model still
#      BUILDING, scope mismatch) is visible.
#
# Required env (../../.env):
#   COVEO_ORG_ID
#   COVEO_ML_MODELS_API_KEY   needs:
#       - Machine Learning > Models > Edit
#       (this is the key we minted 2026-06-01 for the closed-loop apply step)
#
# Usage:
#   scripts/ml/seed_query_suggest.sh             # apply
#   scripts/ml/seed_query_suggest.sh --dry-run   # show what would be uploaded
#   scripts/ml/seed_query_suggest.sh --inspect   # GET current model config + exit
#
# Re-run anytime you edit config/ml/default-queries.json.

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
INSPECT=false
case "${1:-}" in
  --dry-run) DRY_RUN=true ;;
  --inspect) INSPECT=true ;;
esac

AUTH="Authorization: Bearer ${COVEO_ML_MODELS_API_KEY}"
PLATFORM="https://platform.cloud.coveo.com"
MODEL_NAME="pokemon-qs"

# ---------------------------------------------------------------------------
# Step 1: discover the pokemon-qs model ID by display name.
# ---------------------------------------------------------------------------
echo "[1/3] Looking up '$MODEL_NAME' model ID..."
models_resp=$(curl -sS -w "\n%{http_code}" -H "$AUTH" \
  "$PLATFORM/rest/organizations/${COVEO_ORG_ID}/machinelearning/models")
models_body=$(echo "$models_resp" | sed '$d')
models_code=$(echo "$models_resp" | tail -n1)

if [[ "$models_code" != "200" ]]; then
  echo "  ✗ List models failed (HTTP $models_code):" >&2
  echo "$models_body" | head -10 >&2
  if [[ "$models_code" == "401" || "$models_code" == "403" ]]; then
    echo "" >&2
    echo "  Your COVEO_ML_MODELS_API_KEY likely lacks 'Machine Learning > Models > Edit'." >&2
    echo "  See docs/api-keys.md → Key 5." >&2
  fi
  exit 1
fi

MODEL_ID=$(echo "$models_body" | MODEL_NAME="$MODEL_NAME" python3 -c "
import json, os, sys
models = json.load(sys.stdin)
m = next((m for m in models if m.get('modelDisplayName') == os.environ['MODEL_NAME']), None)
if not m:
    print(f\"ERROR: no model with displayName '{os.environ['MODEL_NAME']}'\", file=sys.stderr)
    print(f\"Available: {[x.get('modelDisplayName') for x in models]}\", file=sys.stderr)
    sys.exit(1)
print(m['id'])
")
echo "  ✓ $MODEL_NAME → $MODEL_ID"

# ---------------------------------------------------------------------------
# --inspect: GET current config + exit. Useful for spike work (figuring out
# which JSON field Coveo actually expects for the seed list, since the
# documented endpoint shape varies across product surfaces).
# ---------------------------------------------------------------------------
if $INSPECT; then
  echo ""
  echo "[inspect] Current model config:"
  curl -sS -H "$AUTH" \
    "$PLATFORM/rest/organizations/${COVEO_ORG_ID}/machinelearning/models/${MODEL_ID}" \
    | python3 -m json.tool
  exit 0
fi

# ---------------------------------------------------------------------------
# Step 2: flatten the seed queries into a deduped, newline-separated string.
#
# The JSON file groups queries by category for human readability. Coveo's
# coveo.drill.defaultQueries parameter wants a SINGLE STRING (verified by
# the 2026-06-04 spike — a JSON array gets rejected with "has type LIST
# rather than STRING"). Newline-separated is the format the Console's
# default-queries CSV upload normalizes to internally; the round-trip
# survives Coveo's PUT echo unchanged.
# ---------------------------------------------------------------------------
echo ""
echo "[2/3] Building the seed payload..."
SEED_PAYLOAD=$(python3 -c "
import json, sys
data = json.load(open('$QUERIES_FILE'))
all_queries = list(data.get('names', [])) + list(data.get('type_and_generation', [])) + list(data.get('natural_language_questions', []))
# Dedupe while preserving order (so a re-run with the same JSON produces
# a deterministic payload — easier to diff against past uploads).
seen = set()
deduped = []
for q in all_queries:
    if q not in seen:
        seen.add(q)
        deduped.append(q)
print(json.dumps({'defaultQueries': '\n'.join(deduped)}))
")
NUM_QUERIES=$(echo "$SEED_PAYLOAD" | python3 -c "import json,sys; print(json.load(sys.stdin)['defaultQueries'].count(chr(10)) + 1)")
echo "  ✓ $NUM_QUERIES unique queries ready to upload (newline-separated)."

if $DRY_RUN; then
  echo ""
  echo "[dry-run] Would PUT this payload (first 200 chars):"
  echo "$SEED_PAYLOAD" | head -c 200
  echo "..."
  echo ""
  echo "Dry run complete. No changes applied."
  exit 0
fi

# ---------------------------------------------------------------------------
# Step 3: read-modify-write the model config.
#
# Coveo's ML Models API accepts a single PUT that REPLACES the entire model
# configuration. So we have to GET the current config, modify
# extraConfig.defaultQueries, and PUT the whole thing back. (Empirically
# verified via a spike on 2026-06-04 — extraConfig.defaultQueries is the
# documented field name; the response 200 confirms acceptance.)
#
# Server-managed fields must be dropped from the PUT body or Coveo rejects
# the request — version timestamps, status, modelSizeStatistic, etc. all
# fall in that bucket. Anything in the SERVER_MANAGED list below was
# discovered empirically.
# ---------------------------------------------------------------------------
echo ""
echo "[3/3] Uploading seed queries to $MODEL_NAME..."

# Build the request via Python so we can deserialize the GET, swap the
# extraConfig, drop server-managed fields, and emit a clean PUT body.
PY_RESULT=$(MODEL_ID="$MODEL_ID" COVEO_ML_MODELS_API_KEY="$COVEO_ML_MODELS_API_KEY" \
            COVEO_ORG_ID="$COVEO_ORG_ID" SEED_PAYLOAD="$SEED_PAYLOAD" \
            python3 <<'PYEOF'
import json, os, sys, urllib.request, urllib.error

base = "https://platform.cloud.coveo.com"
mid  = os.environ["MODEL_ID"]
org  = os.environ["COVEO_ORG_ID"]
key  = os.environ["COVEO_ML_MODELS_API_KEY"]
url  = f"{base}/rest/organizations/{org}/machinelearning/models/{mid}"

seed_payload = json.loads(os.environ["SEED_PAYLOAD"])
queries = seed_payload["defaultQueries"]

# GET current config
try:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    current = json.loads(urllib.request.urlopen(req).read())
except urllib.error.HTTPError as e:
    print(f"GET_FAIL {e.code} {e.read().decode()[:300]}", file=sys.stderr)
    sys.exit(2)

# Mutate
existing_extra = current.get("extraConfig", {}) or {}
existing_extra["defaultQueries"] = queries
current["extraConfig"] = existing_extra

# Drop server-managed fields (Coveo rejects them on PUT)
SERVER_MANAGED = [
    "modelVersion", "modelCreationTime", "previousModelUpdateTime",
    "nextModelUpdateTime", "status", "modelActivenessState",
    "registrationKey", "modelSizeStatistic", "modelErrorDescription",
    "info", "platformVersion", "engineVersion",
]
for f in SERVER_MANAGED:
    current.pop(f, None)

# PUT
try:
    body = json.dumps(current).encode()
    req = urllib.request.Request(
        url, data=body, method="PUT",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req)
    print(f"OK {resp.status}")
except urllib.error.HTTPError as e:
    print(f"PUT_FAIL {e.code} {e.read().decode()[:600]}", file=sys.stderr)
    sys.exit(2)
PYEOF
)
PY_RC=$?

if [[ $PY_RC -ne 0 ]]; then
  echo "  ✗ Upload failed:" >&2
  echo "$PY_RESULT" >&2
  exit 1
fi

echo "  ✓ Seed queries accepted ($PY_RESULT)."
echo ""
echo "Done. The next QS model rebuild will incorporate these queries."
echo "Tip: re-run after editing config/ml/default-queries.json. Idempotent."
