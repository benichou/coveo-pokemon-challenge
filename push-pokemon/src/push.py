"""Coveo Push API client.

Three operations we exercise (docs.coveo.com/en/68):

  1. Status update          POST /push/v1/.../sources/{id}/status?statusType=REBUILD
                            Mark the source as REBUILD before pushing, then IDLE
                            after — tells Coveo to flush replaced items cleanly.
  2. Single-item push       PUT /push/v1/.../sources/{id}/documents?documentId=...
                            Body = the Coveo document JSON.
  3. Batch push (efficient) PUT /push/v1/.../sources/{id}/documents/batch
                            Body = {"addOrUpdate": [...], "delete": [...]}
                            One HTTP call replaces many; preferred for >50 docs.

We use the batch endpoint exclusively.
"""

from __future__ import annotations

import json
from collections.abc import Iterable

import httpx

PUSH_BASE = "https://api.cloud.coveo.com/push/v1/organizations"


class CoveoPushClient:
    def __init__(self, org_id: str, source_id: str, api_key: str):
        self.org_id = org_id
        self.source_id = source_id
        self._base = f"{PUSH_BASE}/{org_id}/sources/{source_id}"
        self._auth = {"Authorization": f"Bearer {api_key}"}

    # ----- status -----
    def set_status(self, status_type: str) -> None:
        """status_type ∈ {'REBUILD', 'INCREMENTAL', 'REFRESH', 'IDLE'}."""
        with httpx.Client(timeout=30.0) as c:
            r = c.post(
                f"{self._base}/status",
                params={"statusType": status_type},
                headers=self._auth,
            )
            r.raise_for_status()

    # ----- batch push -----
    def push_batch(self, documents: Iterable[dict]) -> None:
        """Push a batch of documents.

        Coveo's documents/batch endpoint is a 3-step flow (per
        docs.coveo.com/en/68): we ask Coveo for an S3 file container,
        upload our JSON batch to that pre-signed URL, then tell Coveo the
        file is ready by PUTting /documents/batch?fileId=<id>.

        Why three steps: Coveo wants large batches to hit S3 directly, not
        their API gateway. Even small batches go through the same flow.
        """
        docs = list(documents)
        if not docs:
            return

        # Step 1 — request a file container.
        with httpx.Client(timeout=30.0) as c:
            r = c.post(
                f"https://api.cloud.coveo.com/push/v1/organizations/{self.org_id}/files",
                headers=self._auth,
            )
            if r.status_code != 201:
                raise RuntimeError(
                    f"File container request failed (HTTP {r.status_code}): {r.text[:500]}"
                )
            container = r.json()

        upload_uri = container["uploadUri"]
        file_id = container["fileId"]
        # Coveo tells us exactly which headers S3 expects (Content-Type,
        # x-amz-server-side-encryption, etc.). Use those, NOT our bearer auth.
        required_headers = container.get("requiredHeaders", {})

        # Step 2 — upload the batch JSON to S3.
        body = {"addOrUpdate": docs, "delete": []}
        with httpx.Client(timeout=120.0) as c:
            r = c.put(
                upload_uri,
                headers=required_headers,
                content=json.dumps(body),
            )
            if r.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"S3 upload failed (HTTP {r.status_code}): {r.text[:500]}"
                )

        # Step 3 — tell Coveo the file is ready to ingest.
        with httpx.Client(timeout=30.0) as c:
            r = c.put(
                f"{self._base}/documents/batch",
                params={"fileId": file_id},
                headers=self._auth,
            )
            if r.status_code not in (200, 202):
                raise RuntimeError(
                    f"Batch ingest trigger failed (HTTP {r.status_code}): {r.text[:500]}"
                )

    # ----- delete documents -----
    def clear_source(self) -> None:
        """Delete every document currently in the source. Used by `main.py
        --replace` to start a fresh push from a clean slate (so that
        previously-pushed docs that should no longer exist — e.g., items
        the filter logic now correctly excludes — don't linger as orphans).

        Implementation: the Push API's DELETE /documents/olderthan
        endpoint deletes documents whose ordering_id is strictly less than
        the supplied value. Passing a far-future ordering_id (we use a
        large epoch-ms timestamp, year 9999) deletes everything, since
        every existing doc has a smaller ordering_id."""
        very_large_ordering_id = 253402300799000  # year-9999 epoch millis
        with httpx.Client(timeout=30.0) as c:
            r = c.delete(
                f"{self._base}/documents/olderthan",
                params={"orderingId": very_large_ordering_id},
                headers=self._auth,
            )
            if r.status_code not in (200, 202, 204):
                raise RuntimeError(
                    f"clear_source failed (HTTP {r.status_code}): {r.text[:500]}"
                )

    def delete_document(self, document_id: str) -> None:
        """Delete a single document by its documentId. Used for surgical
        cleanup; for full source resets prefer `clear_source()`.

        Why we pass an explicit `orderingId`: Coveo's Push API uses
        per-document ordering IDs to maintain consistency. A DELETE without
        an orderingId is recorded with orderingId=0 (or the request's
        default), and gets *ignored* if the document was pushed later with
        a higher orderingId. Using current epoch millis guarantees our
        delete is newer than any prior push, so it takes effect.
        """
        import time

        now_ms = int(time.time() * 1000)
        with httpx.Client(timeout=30.0) as c:
            r = c.delete(
                f"{self._base}/documents",
                params={"documentId": document_id, "orderingId": now_ms},
                headers=self._auth,
            )
            if r.status_code not in (200, 202, 204):
                raise RuntimeError(
                    f"delete_document failed (HTTP {r.status_code}): {r.text[:500]}"
                )
