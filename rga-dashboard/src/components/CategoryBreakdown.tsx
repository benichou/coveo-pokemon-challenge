import type { EvalRunWithMeta, PerQuestionResult } from "../schemas";
import { pct } from "../format";

type Row = {
  category: string;
  layer: number;
  n: number;
  accuracy: number;
  hard_recall: number;
};

function summarize(per_q: PerQuestionResult[]): Row[] {
  const buckets = new Map<string, PerQuestionResult[]>();
  for (const q of per_q) {
    const k = `${q.layer}::${q.category}`;
    const arr = buckets.get(k);
    if (arr) arr.push(q);
    else buckets.set(k, [q]);
  }
  const rows: Row[] = [];
  for (const [k, qs] of buckets) {
    const [layerStr, category] = k.split("::");
    rows.push({
      category,
      layer: Number(layerStr),
      n: qs.length,
      accuracy: qs.filter((q) => q.verdict.is_correct).length / qs.length,
      hard_recall: qs.reduce((s, q) => s + q.hard_recall, 0) / qs.length,
    });
  }
  // Worst accuracy first, then by layer/category.
  rows.sort((a, b) => a.accuracy - b.accuracy || a.layer - b.layer);
  return rows;
}

function accuracyColor(a: number): string {
  if (a >= 0.9) return "var(--good)";
  if (a >= 0.7) return "var(--ok)";
  if (a >= 0.5) return "var(--warn)";
  return "var(--bad)";
}

type Props = {
  run: EvalRunWithMeta;
};

export function CategoryBreakdown({ run }: Props) {
  const rows = summarize(run.per_question);
  return (
    <section className="category-breakdown">
      <h2>Where it fails — by category</h2>
      <p className="muted">
        Latest run · sorted worst-first. Hover a row for the question count.
      </p>
      <table className="data-table">
        <thead>
          <tr>
            <th>Layer</th>
            <th>Category</th>
            <th>n</th>
            <th>Accuracy</th>
            <th>Hard recall</th>
            <th style={{ width: "30%" }}>Visual</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.layer}-${r.category}`}>
              <td>
                <span className={`layer-pill layer-${r.layer}`}>
                  L{r.layer}
                </span>
              </td>
              <td>
                <code>{r.category}</code>
              </td>
              <td>{r.n}</td>
              <td style={{ color: accuracyColor(r.accuracy), fontWeight: 600 }}>
                {pct(r.accuracy)}
              </td>
              <td>{pct(r.hard_recall)}</td>
              <td>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{
                      width: `${r.accuracy * 100}%`,
                      background: accuracyColor(r.accuracy),
                    }}
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
