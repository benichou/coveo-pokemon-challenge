// Phase 8 — shared in-memory state for the Passage Retrieval result.
//
// Why a separate module: passage-retrieval.js fires the API call, but
// observability.js needs the result inside the search-event log record it
// emits to Grafana (cross-phase TODO from Phase 6E). Rather than coupling
// the two modules or threading the result through engine.state, both
// touch this tiny store.
//
// Keyed by searchUid so a stale write from a prior search can't overwrite
// the current one mid-flight. observability.js reads `latestForUid()`
// when building its log payload; if the passage retrieval call hasn't
// settled yet, the read returns null and observability logs empty
// passage fields (acceptable — empty is more honest than stale).

let _latest = null; // { searchUid, fired, count, top_text, top_source_uri }

export function setLatest(record) {
  _latest = record;
}

export function latestForUid(searchUid) {
  if (!_latest || !searchUid) return null;
  if (_latest.searchUid !== searchUid) return null;
  return _latest;
}
