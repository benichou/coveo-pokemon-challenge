"""Phase 6F Layer 1 — apply the RGA Custom Prompt to Coveo via API.

This script replaces the manual Coveo-Console-paste step. It reads
prompts/pokemon-rga.yaml, fetches the live model state from Coveo,
diffs them, and either:

  - prints the diff and exits (default — dry-run is the safe default)
  - submits the PUT to actually update Coveo (--apply flag)

Why a dry-run default? Because the apply script writes to a live
production model. We want the script's "did nothing accidentally"
behavior to be the no-flag invocation, and "actually do the thing" to
require an explicit flag. The PR-merge workflow in Phase 6F.5 passes
--apply automatically because the PR review IS the human gate.

Usage:
  uv run python src/apply.py                  # dry-run (default) — shows the diff
  uv run python src/apply.py --apply          # actually submit the PUT
  uv run python src/apply.py --prompt-file path/to/other.yaml  # use a non-default YAML

Endpoint:
  PUT /rest/organizations/{orgId}/machinelearning/models/{modelId}
  Body: full model object with extraConfig.additionalAnswerInstructions
        replaced.
  Auth: COVEO_ML_MODELS_API_KEY (Machine Learning Models: Edit). The
        admin key (Sources + Fields Edit) is NOT enough — it gets a
        403 on PUT despite working for GET. The judge key
        (Knowledge.Answer Manager) doesn't even work for GET. A
        dedicated least-privilege key is the cleanest fit.
        See docs/api-keys.md "Phase 6F.1" section.
"""

from __future__ import annotations

import argparse
import difflib
import os
import sys
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv
from schemas import PromptVersion

PLATFORM = "https://platform.cloud.coveo.com"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

DEFAULT_PROMPT_YAML = (
    Path(__file__).resolve().parent.parent / "prompts" / "pokemon-rga.yaml"
)


# ---------- Pure functions (testable without network) ----------


def load_prompt(path: Path) -> PromptVersion:
    """Read + validate a prompts/*.yaml file."""
    raw = yaml.safe_load(path.read_text())
    return PromptVersion.model_validate(raw)


def make_diff(current: str, new: str) -> str:
    """Return a unified diff of the prompt change, as a single string."""
    return "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="current (live in Coveo)",
            tofile="new (from YAML)",
            lineterm="",
        )
    )


def patch_model_body(current_model: dict, new_prompt: str) -> dict:
    """Return a deep-ish copy of the model with the prompt swapped.

    The PUT endpoint takes the full model body back. We mutate only
    extraConfig.additionalAnswerInstructions and leave everything else
    untouched so we don't accidentally overwrite unrelated config.
    """
    new_body = {**current_model}
    new_body["extraConfig"] = {
        **(current_model.get("extraConfig") or {}),
        "additionalAnswerInstructions": new_prompt,
    }
    return new_body


# ---------- Coveo API wrappers (live calls) ----------


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def find_model_id(
    org_id: str,
    api_key: str,
    display_name: str,
    *,
    client: httpx.Client | None = None,
) -> str:
    """Discover the model id by listing models + filtering on displayName.

    Stable across model rebuilds — the volatile model id changes when a
    model is recreated, but the modelDisplayName we set in the Console
    is preserved.
    """
    c = client or httpx.Client(timeout=15.0)
    try:
        r = c.get(
            f"{PLATFORM}/rest/organizations/{org_id}/machinelearning/models",
            headers=_auth_headers(api_key),
        )
        r.raise_for_status()
        models = r.json()
        for m in models:
            if m.get("modelDisplayName") == display_name:
                return m["id"]
        raise RuntimeError(
            f"No model with modelDisplayName={display_name!r} found on org {org_id}. "
            f"Available: {sorted(m.get('modelDisplayName', '<unnamed>') for m in models)}"
        )
    finally:
        if client is None:
            c.close()


def fetch_model(
    org_id: str,
    api_key: str,
    model_id: str,
    *,
    client: httpx.Client | None = None,
) -> dict:
    """Fetch the full model object by id."""
    c = client or httpx.Client(timeout=15.0)
    try:
        r = c.get(
            f"{PLATFORM}/rest/organizations/{org_id}/machinelearning/models/{model_id}",
            headers=_auth_headers(api_key),
        )
        r.raise_for_status()
        return r.json()
    finally:
        if client is None:
            c.close()


def put_model(
    org_id: str,
    api_key: str,
    model_id: str,
    body: dict,
    *,
    client: httpx.Client | None = None,
) -> None:
    """Submit a full-body PUT to update the model.

    Returns None on success. Raises HTTPStatusError on non-2xx.
    """
    c = client or httpx.Client(timeout=30.0)
    try:
        r = c.put(
            f"{PLATFORM}/rest/organizations/{org_id}/machinelearning/models/{model_id}",
            headers={
                **_auth_headers(api_key),
                "Content-Type": "application/json",
            },
            json=body,
        )
        r.raise_for_status()
    finally:
        if client is None:
            c.close()


# ---------- Orchestrator ----------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually submit the PUT. Default is dry-run: print the diff and exit. "
            "Pass --apply only after reviewing the diff."
        ),
    )
    ap.add_argument(
        "--prompt-file",
        type=Path,
        default=DEFAULT_PROMPT_YAML,
        help=f"Path to the YAML prompt file (default: {DEFAULT_PROMPT_YAML}).",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help=(
            "Bypass the 'live already matches YAML' early-exit and submit the "
            "PUT anyway. Useful for: verifying the write path (e.g., after API "
            "changes), rollback drills, and ensuring the live value is "
            "byte-identical to the YAML (not just semantically equal)."
        ),
    )
    args = ap.parse_args()

    # Env
    org_id = os.environ.get("COVEO_ORG_ID")
    api_key = os.environ.get("COVEO_ML_MODELS_API_KEY")
    if not org_id or not api_key:
        print(
            "ERROR: COVEO_ORG_ID and COVEO_ML_MODELS_API_KEY must be set in "
            "env (usually via .env). The ML Models key requires the "
            "Machine Learning Models: Edit privilege — see docs/api-keys.md.",
            file=sys.stderr,
        )
        return 1

    # Load + validate YAML
    if not args.prompt_file.exists():
        print(
            f"ERROR: prompt file not found: {args.prompt_file}", file=sys.stderr
        )
        return 1
    pv = load_prompt(args.prompt_file)
    desired = pv.prompt.strip()
    print(f"→ Loaded prompt from {args.prompt_file}")
    print(f"  version: {pv.metadata.version}")
    print(
        f"  target model: displayName={pv.model.display_name!r} engine={pv.model.engine_id!r}"
    )
    print(f"  prompt length: {len(desired)} chars")

    # Discover + fetch live state
    print("\n→ Discovering model id on Coveo...")
    try:
        model_id = find_model_id(org_id, api_key, pv.model.display_name)
    except (httpx.HTTPError, RuntimeError) as e:
        print(f"ERROR: model discovery failed: {e}", file=sys.stderr)
        return 1
    print(f"  model_id={model_id}")

    print("\n→ Fetching current live state...")
    try:
        current_model = fetch_model(org_id, api_key, model_id)
    except httpx.HTTPError as e:
        print(f"ERROR: GET model failed: {e}", file=sys.stderr)
        return 1
    current_prompt = (
        (current_model.get("extraConfig") or {})
        .get("additionalAnswerInstructions", "")
        .strip()
    )
    print(f"  current prompt length: {len(current_prompt)} chars")

    # Diff
    prompts_match = current_prompt == desired
    if prompts_match and not args.force:
        print("\n✓ Live prompt already matches YAML. No change needed.")
        return 0

    if prompts_match and args.force:
        print(
            "\n→ Prompts match but --force is set. Will submit a no-op PUT "
            "to exercise the write path."
        )
    else:
        print("\n✗ Prompts differ. Diff (live → YAML):\n")
        print(make_diff(current_prompt, desired))

    if not args.apply:
        print(
            "\n--apply flag NOT set. Dry-run complete; no write to Coveo.\n"
            "  To submit the PUT, re-run with --apply."
        )
        return 0

    # Apply
    print("\n→ Submitting PUT to Coveo...")
    new_body = patch_model_body(current_model, desired)
    try:
        put_model(org_id, api_key, model_id, new_body)
    except httpx.HTTPStatusError as e:
        print(
            f"ERROR: PUT failed (HTTP {e.response.status_code}):\n"
            f"  {e.response.text[:500]}",
            file=sys.stderr,
        )
        return 1
    except httpx.HTTPError as e:
        print(f"ERROR: PUT failed: {e}", file=sys.stderr)
        return 1

    # Verify by re-fetching
    print("→ Verifying by re-fetching...")
    after = fetch_model(org_id, api_key, model_id)
    after_prompt = (
        (after.get("extraConfig") or {})
        .get("additionalAnswerInstructions", "")
        .strip()
    )
    if after_prompt == desired:
        print("\n✓ Verified: live prompt now matches YAML.")
        return 0
    print(
        "\n✗ Verification FAILED: PUT succeeded but live prompt doesn't match "
        "what we sent. Live value may be transformed by Coveo (e.g., whitespace "
        "normalization). Inspect manually.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
