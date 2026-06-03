#!/usr/bin/env bash
#
# scripts/associate_ml_models.sh — wire the pokemon-rga and pokemon-se ML
# models into the default query pipeline so they actually do something at
# search time.
#
# Why this exists
# ---------------
# Coveo splits ML into two layers: the MODEL (a piece of trained data — exists
# in isolation, does nothing on its own) and the ASSOCIATION (the wiring that
# tells a query pipeline "when a query comes through, run it through this
# model"). RGA and Semantic Encoder model CREATION is Console-only per
# Coveo's public docs, but association IS API-documented — so we script it.
#
# Why script it
#   - Reproducibility: re-run on a fresh org and the associations come back.
#   - Idempotency: detects existing associations and skips them.
#   - Panel artifact: shows we understand Coveo's separation between models
#     and pipelines, and that we exercise the documented API surface.
#
# What it does
#   1. Looks up the default query pipeline by `isDefault=true`.
#   2. Looks up the pokemon-rga and pokemon-se model IDs by display name.
#   3. Lists existing model associations on that pipeline.
#   4. Creates associations for any missing model, skips any already present.
#   5. Re-lists associations and prints the final state.
#
# Required env (../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY   needs:
#       - Search > Query pipelines > Edit
#       - Machine Learning > Models > View
#
# Usage:
#   scripts/associate_ml_models.sh             # apply
#   scripts/associate_ml_models.sh --dry-run   # show what would happen
#
# If models are still BUILDING, the association is still accepted — Coveo
# just makes it active once the model reaches the READY state.

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
: "${COVEO_ADMIN_API_KEY:?missing in .env}"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

AUTH="Authorization: Bearer ${COVEO_ADMIN_API_KEY}"
PLATFORM="https://platform.cloud.coveo.com"
ORG_QS="organizationId=${COVEO_ORG_ID}"

# The models we expect to associate. Hardcoded by display name — we created
# them in the Console under these exact names (see docs/ml-models.md).
RGA_NAME="pokemon-rga"
SE_NAME="pokemon-se"
QS_NAME="pokemon-qs"

# ---------------------------------------------------------------------------
# Step 1: find the default query pipeline ID
# ---------------------------------------------------------------------------
echo "[1/4] Looking up the default query pipeline..."
pipelines_resp=$(curl -sS -w "\n%{http_code}" -H "$AUTH" \
  "$PLATFORM/rest/search/v1/admin/pipelines?${ORG_QS}")
pipelines_body=$(echo "$pipelines_resp" | sed '$d')
pipelines_code=$(echo "$pipelines_resp" | tail -n1)

if [[ "$pipelines_code" != "200" ]]; then
  echo "  ✗ List pipelines failed (HTTP $pipelines_code):" >&2
  echo "$pipelines_body" | head -5 >&2
  if [[ "$pipelines_code" == "401" || "$pipelines_code" == "403" ]]; then
    echo "" >&2
    echo "  Your COVEO_ADMIN_API_KEY likely lacks 'Search > Query pipelines > Edit'." >&2
    echo "  See docs/api-keys.md for how to mint a key with the right privileges." >&2
  fi
  exit 1
fi

PIPELINE_ID=$(echo "$pipelines_body" | python3 -c "
import json, sys
pipelines = json.load(sys.stdin)
default = next((p for p in pipelines if p.get('isDefault')), None)
if not default:
    print('ERROR: no default pipeline found', file=sys.stderr)
    sys.exit(1)
print(default['id'])
")
PIPELINE_NAME=$(echo "$pipelines_body" | python3 -c "
import json, sys
pipelines = json.load(sys.stdin)
default = next((p for p in pipelines if p.get('isDefault')), None)
print(default.get('name', 'default'))
")
echo "  ✓ Default pipeline: '$PIPELINE_NAME' (id=$PIPELINE_ID)"

# ---------------------------------------------------------------------------
# Step 2: find the model IDs by display name
# ---------------------------------------------------------------------------
echo ""
echo "[2/4] Looking up model IDs..."
models_resp=$(curl -sS -w "\n%{http_code}" -H "$AUTH" \
  "$PLATFORM/rest/organizations/${COVEO_ORG_ID}/machinelearning/models")
models_body=$(echo "$models_resp" | sed '$d')
models_code=$(echo "$models_resp" | tail -n1)

if [[ "$models_code" != "200" ]]; then
  echo "  ✗ List models failed (HTTP $models_code):" >&2
  echo "$models_body" | head -5 >&2
  exit 1
fi

RGA_ID=$(echo "$models_body" | RGA_NAME="$RGA_NAME" python3 -c "
import json, os, sys
models = json.load(sys.stdin)
m = next((m for m in models if m.get('modelDisplayName') == os.environ['RGA_NAME']), None)
if not m:
    print(f\"ERROR: no model with displayName '{os.environ['RGA_NAME']}'\", file=sys.stderr)
    sys.exit(1)
print(m['id'])  # Coveo's ML endpoint returns 'id', not 'modelId'
")
SE_ID=$(echo "$models_body" | SE_NAME="$SE_NAME" python3 -c "
import json, os, sys
models = json.load(sys.stdin)
m = next((m for m in models if m.get('modelDisplayName') == os.environ['SE_NAME']), None)
if not m:
    print(f\"ERROR: no model with displayName '{os.environ['SE_NAME']}'\", file=sys.stderr)
    sys.exit(1)
print(m['id'])  # Coveo's ML endpoint returns 'id', not 'modelId'
")

# pokemon-qs (Query Suggest, Phase 6B) — added later than RGA + SE; warn if
# missing rather than exit, so this script stays usable on orgs where QS
# hasn't been created yet.
QS_ID=$(echo "$models_body" | QS_NAME="$QS_NAME" python3 -c "
import json, os, sys
models = json.load(sys.stdin)
m = next((m for m in models if m.get('modelDisplayName') == os.environ['QS_NAME']), None)
print(m['id'] if m else '')
")

echo "  ✓ $RGA_NAME → $RGA_ID"
echo "  ✓ $SE_NAME  → $SE_ID"
if [[ -n "$QS_ID" ]]; then
  echo "  ✓ $QS_NAME  → $QS_ID"
else
  echo "  ⚠ $QS_NAME  not found — skipping (create it in the Console first; see docs/ml-models.md)"
fi

# ---------------------------------------------------------------------------
# Step 3: list existing associations on this pipeline (for idempotency)
# ---------------------------------------------------------------------------
echo ""
echo "[3/4] Reading existing model associations on '$PIPELINE_NAME'..."
existing_resp=$(curl -sS -w "\n%{http_code}" -H "$AUTH" \
  "$PLATFORM/rest/search/v2/admin/pipelines/${PIPELINE_ID}/ml/model/associations?${ORG_QS}")
existing_body=$(echo "$existing_resp" | sed '$d')
existing_code=$(echo "$existing_resp" | tail -n1)

if [[ "$existing_code" != "200" ]]; then
  echo "  ✗ List associations failed (HTTP $existing_code):" >&2
  echo "$existing_body" | head -5 >&2
  exit 1
fi

EXISTING_IDS=$(echo "$existing_body" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# The /v2/.../associations endpoint returns {rules: [...], totalEntries, totalPages}.
rules = data.get('rules', []) if isinstance(data, dict) else data
for a in rules:
    mid = a.get('modelId') or (a.get('parameters') or {}).get('modelId')
    if mid:
        print(mid)
")
echo "  ✓ Found $(echo -n "$EXISTING_IDS" | grep -c . || true) existing association(s)."

# ---------------------------------------------------------------------------
# Step 4: create the two associations idempotently
# ---------------------------------------------------------------------------
associate() {
  local model_name="$1"
  local model_id="$2"
  if echo "$EXISTING_IDS" | grep -qx "$model_id"; then
    echo "  [skip]   $model_name already associated."
    return 0
  fi
  if $DRY_RUN; then
    echo "  [dry]    would associate $model_name ($model_id)"
    return 0
  fi
  echo "  [create] associating $model_name ($model_id)..."
  body=$(python3 -c "
import json
print(json.dumps({'modelId': '$model_id', 'useAdvancedConfiguration': False}))
")
  resp=$(curl -sS -w "\n%{http_code}" -X POST \
    -H "$AUTH" \
    -H "Content-Type: application/json" \
    "$PLATFORM/rest/search/v2/admin/pipelines/${PIPELINE_ID}/ml/model/associations?${ORG_QS}" \
    --data "$body")
  code=$(echo "$resp" | tail -n1)
  if [[ "$code" != "200" && "$code" != "201" ]]; then
    echo "  ✗ POST failed (HTTP $code):" >&2
    echo "$resp" | sed '$d' | head -10 >&2
    return 1
  fi
  echo "  ✓ $model_name associated."
}

echo ""
echo "[4/4] Creating missing associations..."
associate "$RGA_NAME" "$RGA_ID"
associate "$SE_NAME"  "$SE_ID"
if [[ -n "$QS_ID" ]]; then
  associate "$QS_NAME" "$QS_ID"
fi

# ---------------------------------------------------------------------------
# Final state
# ---------------------------------------------------------------------------
echo ""
echo "Final association state on '$PIPELINE_NAME':"
curl -sS -H "$AUTH" \
  "$PLATFORM/rest/search/v2/admin/pipelines/${PIPELINE_ID}/ml/model/associations?${ORG_QS}" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
rules = data.get('rules', []) if isinstance(data, dict) else data
if not rules:
    print('  (none)')
for a in rules:
    mid = a.get('modelId') or (a.get('parameters') or {}).get('modelId') or '?'
    name = a.get('modelDisplayName') or (a.get('parameters') or {}).get('modelDisplayName') or '?'
    typ  = a.get('engineId') or '?'
    print(f'  - {name:20s} type={typ:20s} id={mid}')
"

echo ""
if $DRY_RUN; then
  echo "Dry run complete. No changes applied."
else
  echo "Done. Models will become active once their build state is READY."
  echo "Tip: re-run this script anytime — it's idempotent."
fi
