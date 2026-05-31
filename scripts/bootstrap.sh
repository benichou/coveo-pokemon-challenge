#!/usr/bin/env bash
#
# End-to-end bootstrap of the Coveo org for the Pokemon Challenge build.
# Idempotent: safe to re-run; skips any resource that already exists in the
# desired state.
#
# Order matters:
#   1. validate/org_features.sh    — required Coveo features are licensed
#   2. validate/api_keys.sh        — all API keys have correct privileges
#   3. setup/fields.sh             — POST any missing fields
#   4. setup/source.sh             — POST the Sitemap source (writes id to .env)
#   5. setup/scraping.sh           — apply config/source/scraping.json
#   6. setup/mappings.sh           — POST any missing mappings
#   7. source/widen.sh narrow      — initial scope = single Pokemon (safe)
#       SAFETY GUARD: if the source's current URL filter is already wider
#       than `narrow` (i.e., the org has been bootstrapped before and the
#       crawl was widened), this step is SKIPPED by default to avoid
#       collapsing a populated index back to one item. Pass --reset-filter
#       to force the downgrade.
#   8. source/rebuild.sh           — trigger and wait for first build
#
# Required environment variables (sourced from ../.env):
#   COVEO_ORG_ID
#   COVEO_ADMIN_API_KEY
#   COVEO_SITEMAP_SOURCE_ID (after the first run; setup/source.sh writes it)
#
# Note: this script does NOT create API keys (Coveo requires Console UI for
# minting because the secret is shown only once). Run this script AFTER you've
# created the keys manually and put them in .env (see docs/api-keys.md).
#
# Usage:
#   scripts/bootstrap.sh
#   scripts/bootstrap.sh --skip-rebuild      # everything except the rebuild
#   scripts/bootstrap.sh --reset-filter      # force the filter back to narrow
#                                            # (use only when you actually want
#                                            #  to reset a populated index)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKIP_REBUILD=false
RESET_FILTER=false
for arg in "$@"; do
  case "$arg" in
    --skip-rebuild) SKIP_REBUILD=true ;;
    --reset-filter) RESET_FILTER=true ;;
    --help|-h)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      echo "Run $0 --help for usage." >&2
      exit 1
      ;;
  esac
done

run_step() {
  local title=$1
  shift
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  $title"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  "$@"
}

# ----------------------------------------------------------------------------
# Detect the source's current URL filter mode and decide whether step 7 should
# run. Returns one of: narrow | spot-check | all | unknown | absent.
# ----------------------------------------------------------------------------
detect_current_filter_mode() {
  # If the source doesn't exist yet, the filter mode is "absent" — step 7
  # should run normally (sets the initial narrow filter on the new source).
  if [[ -z "${COVEO_SITEMAP_SOURCE_ID:-}" ]]; then
    echo "absent"
    return
  fi

  local resp
  resp=$(curl -sS \
    -H "Authorization: Bearer ${COVEO_ADMIN_API_KEY}" \
    "https://platform.cloud.coveo.com/rest/organizations/${COVEO_ORG_ID}/sources/${COVEO_SITEMAP_SOURCE_ID}" \
    2>/dev/null) || { echo "unknown"; return; }

  FILTER_CONFIG="$REPO_ROOT/config/source/url_filter.json" \
    SOURCE_RESP="$resp" \
    python3 <<'PY'
import json, os, sys

try:
    src = json.loads(os.environ["SOURCE_RESP"])
except json.JSONDecodeError:
    print("unknown"); sys.exit(0)

current = next(
    (f.get("filter") for f in src.get("urlFilters", [])
     if f.get("includeFilter")),
    None,
)
if not current:
    print("absent"); sys.exit(0)

with open(os.environ["FILTER_CONFIG"]) as f:
    cfg = json.load(f)
for mode, m in cfg.get("modes", {}).items():
    if m.get("include_regex") == current:
        print(mode); sys.exit(0)
print("unknown")
PY
}

run_step "1/8  Validate org features (Passage Retrieval, RGA, ART)" \
  "$SCRIPT_DIR/validate/org_features.sh"

run_step "2/8  Validate API keys (push, admin, search)" \
  "$SCRIPT_DIR/validate/api_keys.sh"

run_step "3/8  Create fields (idempotent)" \
  "$SCRIPT_DIR/setup/fields.sh"

run_step "4/8  Create Sitemap source (idempotent; writes id to .env)" \
  "$SCRIPT_DIR/setup/source.sh"

# Re-source .env in case setup/source.sh just wrote COVEO_SITEMAP_SOURCE_ID.
# We need it for the filter-mode check below.
if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a; source "$REPO_ROOT/.env"; set +a
fi

run_step "5/8  Apply web scraping configuration" \
  "$SCRIPT_DIR/setup/scraping.sh"

run_step "6/8  Add mappings (idempotent)" \
  "$SCRIPT_DIR/setup/mappings.sh"

# Step 7 — apply `narrow` filter. SAFETY GUARD: if the source is already at
# `spot-check` or `all`, skip unless --reset-filter was passed. This prevents
# bootstrap.sh from inadvertently collapsing a populated production index
# (see scripts/README.md for the 2026-05-30 incident that motivated this).
current_mode=$(detect_current_filter_mode)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
case "$current_mode" in
  absent|narrow|unknown)
    if [[ "$current_mode" == "unknown" ]]; then
      echo "  7/8  Current filter not recognized — applying 'narrow' as safe default"
    else
      echo "  7/8  Set URL inclusion to 'narrow' (single Pokemon — safe initial scope)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    "$SCRIPT_DIR/source/widen.sh" narrow
    ;;
  spot-check|all)
    if [[ "$RESET_FILTER" == "true" ]]; then
      echo "  7/8  Forcing filter back to 'narrow' (--reset-filter)"
      echo "       Previous mode was: $current_mode"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      "$SCRIPT_DIR/source/widen.sh" narrow
    else
      echo "  7/8  Filter is already at '$current_mode' — preserving (pass --reset-filter to override)"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "       Skipping the narrow downgrade so an existing populated index is preserved."
    fi
    ;;
esac

if [[ "$SKIP_REBUILD" == "true" ]]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  8/8  Skipping rebuild (--skip-rebuild)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
  run_step "8/8  Trigger rebuild and wait until idle" \
    "$SCRIPT_DIR/source/rebuild.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ Bootstrap complete."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  - Open Content Browser to inspect the indexed Pokemon"
echo "  - When ready to scale up:"
echo "      scripts/source/widen.sh spot-check     # 8 diverse Pokemon"
echo "      scripts/source/rebuild.sh"
echo "    then:"
echo "      scripts/source/widen.sh all            # all ~1,025 Pokemon"
echo "      scripts/source/rebuild.sh              # ~17 min crawl"
