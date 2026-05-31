import { Fragment, useMemo, useState } from "react";
import type { EvalRunWithMeta, PerQuestionResult } from "../schemas";
import { pct } from "../format";

type Filter = "all" | "incorrect" | "hallucinations";
type LayerFilter = "all" | 1 | 2 | 3;

type Props = {
  run: EvalRunWithMeta;
};

function applyFilters(
  rows: PerQuestionResult[],
  filter: Filter,
  layer: LayerFilter,
): PerQuestionResult[] {
  return rows
    .filter((r) => layer === "all" || r.layer === layer)
    .filter((r) => {
      if (filter === "all") return true;
      if (filter === "incorrect") return !r.verdict.is_correct;
      return r.verdict.has_hallucination;
    });
}

function truncate(s: string, n: number): string {
  if (s.length <= n) return s;
  return s.slice(0, n).trimEnd() + "…";
}

export function FailuresTable({ run }: Props) {
  const [filter, setFilter] = useState<Filter>("incorrect");
  const [layer, setLayer] = useState<LayerFilter>("all");
  const [expanded, setExpanded] = useState<string | null>(null);

  const rows = useMemo(
    () => applyFilters(run.per_question, filter, layer),
    [run, filter, layer],
  );

  return (
    <section className="failures">
      <h2>Drill-down — per-question results</h2>
      <div className="filter-row">
        <label>
          Show:
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as Filter)}
          >
            <option value="incorrect">Incorrect only</option>
            <option value="hallucinations">Hallucinations only</option>
            <option value="all">All ({run.per_question.length})</option>
          </select>
        </label>
        <label>
          Layer:
          <select
            value={String(layer)}
            onChange={(e) =>
              setLayer(
                e.target.value === "all"
                  ? "all"
                  : (Number(e.target.value) as LayerFilter),
              )
            }
          >
            <option value="all">All</option>
            <option value="1">Layer 1</option>
            <option value="2">Layer 2</option>
            <option value="3">Layer 3</option>
          </select>
        </label>
        <span className="muted">Showing {rows.length} question(s)</span>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>L</th>
            <th>Category</th>
            <th>Question</th>
            <th>Correct?</th>
            <th>Hallu?</th>
            <th>Recall</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const isExpanded = expanded === r.question_id;
            return (
              <Fragment key={r.question_id}>
                <tr
                  className="row-clickable"
                  onClick={() =>
                    setExpanded(isExpanded ? null : r.question_id)
                  }
                >
                  <td>
                    <code>{r.question_id}</code>
                  </td>
                  <td>
                    <span className={`layer-pill layer-${r.layer}`}>
                      L{r.layer}
                    </span>
                  </td>
                  <td>
                    <code>{r.category}</code>
                  </td>
                  <td>{truncate(r.question, 80)}</td>
                  <td>
                    {r.verdict.is_correct ? (
                      <span className="badge-good">✓</span>
                    ) : (
                      <span className="badge-bad">✗</span>
                    )}
                  </td>
                  <td>
                    {r.verdict.has_hallucination ? (
                      <span className="badge-bad">!</span>
                    ) : (
                      <span className="badge-muted">—</span>
                    )}
                  </td>
                  <td>{pct(r.hard_recall)}</td>
                </tr>
                {isExpanded && (
                  <tr className="detail-row">
                    <td colSpan={7}>
                      <div className="detail-grid">
                        <div>
                          <h4>Question</h4>
                          <p>{r.question}</p>
                        </div>
                        <div>
                          <h4>Judge reasoning</h4>
                          <p>{r.verdict.reasoning}</p>
                        </div>
                        {r.verdict.false_claims.length > 0 && (
                          <div>
                            <h4>False claims found</h4>
                            <ul>
                              {r.verdict.false_claims.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <div>
                          <h4>RGA answer</h4>
                          <pre className="answer-block">
                            {r.answer_text ||
                              "(empty — RGA did not produce an answer)"}
                          </pre>
                        </div>
                        {r.cited_uris.length > 0 && (
                          <div>
                            <h4>Cited sources</h4>
                            <ul className="citation-list">
                              {r.cited_uris.map((u, i) => (
                                <li key={i}>
                                  <code>{u}</code>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
