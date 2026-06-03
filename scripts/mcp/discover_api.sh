#!/usr/bin/env bash
#
# scripts/mcp/discover_api.sh — read-only spike to identify Coveo's admin
# REST API surface for the Hosted MCP Server (Phase 8.5).
#
# Why this exists
# ---------------
# Coveo's MCP Server is configurable via the Admin Console UI (Overview /
# Tools / Server implementation tabs), but the public docs at
# docs.coveo.com/en/q1mb0212/ don't describe an admin REST API for the same
# functionality. The Console UI must be calling SOME backend; this script
# probes the most likely endpoint shapes to find it.
#
# All probes are GET-only (read-only). No risk to the configured server.
#
# Finding (2026-06-03 run)
# ------------------------
# All 8 candidate endpoint patterns returned 404 INVALID_URI against both
# COVEO_ADMIN_API_KEY and COVEO_ML_MODELS_API_KEY. Coveo does NOT publish
# an MCP Server admin REST API at any conventional path yet. The Console
# uses an internal/non-public endpoint that we can't predict from URL
# shape alone, and we deliberately chose NOT to scrape internal APIs (would
# break the moment Coveo refactors them).
#
# So Phase 8.5's source-of-truth for MCP server config is
# config/mcp/pokemon-mcp.yaml, applied to Coveo via a documented manual
# workflow (paste into the Console). See config/mcp/README.md for the flow.
#
# Re-run this script periodically (or wire it into CI) — the day any URL
# returns 200, we can build the apply script (scripts/mcp/apply_mcp_server.sh)
# that PUTs the YAML to Coveo, replacing the manual paste step.
#
# Required env (../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY        — Custom template (broad admin scope)
#   COVEO_ML_MODELS_API_KEY    — Custom template (ML models edit)
#   COVEO_MCP_SERVER_ID        — the per-server UUID from the Console
#                                Overview tab → Details → Endpoint
#                                (NOT a secret; it's in the URL)
#
# Usage:
#   scripts/mcp/discover_api.sh
#
# Output: HTTP status code + first 300 chars of response body for each
# probe. The endpoint that returns 200 with the MCP server config JSON
# is the admin API we'll target for apply_mcp_server.sh.

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

# COVEO_MCP_SERVER_ID is the UUID in the Console endpoint URL after
# /mcp/server/. Console Overview tab → Details → Endpoint shows:
# https://platform.cloud.coveo.com/api/v1/organizations/{org}/mcp/server/{uuid}
# We need to add this to .env (or pass via CLI).
if [[ -z "${COVEO_MCP_SERVER_ID:-}" ]]; then
  # Extract from the endpoint URL if it's set instead
  if [[ -n "${COVEO_MCP_ENDPOINT:-}" ]]; then
    COVEO_MCP_SERVER_ID="${COVEO_MCP_ENDPOINT##*/}"
    echo "Extracted COVEO_MCP_SERVER_ID from COVEO_MCP_ENDPOINT: $COVEO_MCP_SERVER_ID"
  else
    echo "ERROR: set COVEO_MCP_SERVER_ID (the UUID after /mcp/server/ in the Console endpoint) in .env"
    exit 1
  fi
fi

# Candidate endpoint patterns to probe.
# Coveo's conventional admin API root is /rest/organizations/{orgId}/...
# The MCP protocol endpoint we already know uses /api/v1/...; the admin
# surface might be on either root. We try multiple paths because Coveo
# doesn't publicly document the admin shape.
PLATFORM="https://platform.cloud.coveo.com"

CANDIDATES=(
  # /rest/ root, likely admin surface
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/machinelearning/mcp/servers/$COVEO_MCP_SERVER_ID"
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/machinelearning/mcpservers/$COVEO_MCP_SERVER_ID"
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/mcp/servers/$COVEO_MCP_SERVER_ID"
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/mcpservers/$COVEO_MCP_SERVER_ID"
  # /api/v1/ root, alongside the MCP protocol endpoint
  "$PLATFORM/api/v1/organizations/$COVEO_ORG_ID/mcp/servers/$COVEO_MCP_SERVER_ID"
  "$PLATFORM/api/v1/organizations/$COVEO_ORG_ID/mcp/servers/$COVEO_MCP_SERVER_ID/configuration"
  # Listing endpoints — useful even if individual server is at a different path
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/machinelearning/mcp/servers"
  "$PLATFORM/rest/organizations/$COVEO_ORG_ID/mcp/servers"
)

probe() {
  local url="$1"
  local key_label="$2"
  local key_value="$3"

  printf "\n──────────────\n"
  printf "URL: %s\n" "$url"
  printf "Key: %s\n" "$key_label"

  local response status body
  response=$(curl -sS -w "\n__HTTP_STATUS__:%{http_code}\n" \
    -H "Authorization: Bearer $key_value" \
    -H "Accept: application/json" \
    "$url" 2>&1 || true)

  status=$(printf "%s" "$response" | grep "__HTTP_STATUS__:" | cut -d: -f2 || echo "???")
  body=$(printf "%s" "$response" | sed '/__HTTP_STATUS__:/d' | head -c 400)

  printf "Status: %s\n" "$status"
  if [[ "$status" == "200" ]]; then
    printf "Body (first 400 chars):\n%s\n" "$body"
    if command -v jq >/dev/null 2>&1; then
      printf "\nKeys at top level:\n"
      printf "%s" "$body" | jq -r 'keys[]?' 2>/dev/null || true
    fi
  else
    printf "Body: %s\n" "$body"
  fi
}

printf "==============================\n"
printf "Coveo MCP admin API discovery\n"
printf "==============================\n"
printf "OrgID: %s\n" "$COVEO_ORG_ID"
printf "MCP Server ID: %s\n" "$COVEO_MCP_SERVER_ID"

for url in "${CANDIDATES[@]}"; do
  probe "$url" "COVEO_ADMIN_API_KEY" "$COVEO_ADMIN_API_KEY"
done

# If admin key didn't find anything useful, try ml-models key (different scope)
if [[ -n "${COVEO_ML_MODELS_API_KEY:-}" ]]; then
  printf "\n\n==============================\n"
  printf "Retrying with COVEO_ML_MODELS_API_KEY\n"
  printf "==============================\n"
  for url in "${CANDIDATES[@]}"; do
    probe "$url" "COVEO_ML_MODELS_API_KEY" "$COVEO_ML_MODELS_API_KEY"
  done
fi

printf "\n──────────────\nDONE. Look for a 200 response above; that path is the admin API.\n"
