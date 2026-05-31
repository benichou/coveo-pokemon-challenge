import type { EvalRunWithMeta } from "../schemas";
import { pct, deltaPct, deltaSign } from "../format";

type Props = {
  latest: EvalRunWithMeta;
  previous?: EvalRunWithMeta;
};

type MetricKey = "accuracy" | "precision" | "hard_recall" | "citation_precision";

const METRICS: { key: MetricKey; label: string; help: string }[] = [
  {
    key: "accuracy",
    label: "Accuracy",
    help: "Sonnet-judged: is the answer correct overall?",
  },
  {
    key: "precision",
    label: "Precision",
    help: "1 − (fraction of answers with any hallucination)",
  },
  {
    key: "hard_recall",
    label: "Hard recall",
    help: "Substring match on expected facts (deterministic)",
  },
  {
    key: "citation_precision",
    label: "Citation precision",
    help: "Fraction of cited URIs that are in expected_citations",
  },
];

function deltaColor(sign: -1 | 0 | 1): string {
  if (sign > 0) return "var(--good)";
  if (sign < 0) return "var(--bad)";
  return "var(--muted)";
}

export function SummaryCard({ latest, previous }: Props) {
  return (
    <section className="snapshot">
      <header className="snapshot-header">
        <div>
          <h2>Latest run — {latest.date}</h2>
          <p className="snapshot-meta">
            n = {latest.overall.n_questions} questions · judge ={" "}
            <code>{latest.judge_model}</code>
            {previous && (
              <>
                {" "}
                · Δ vs <strong>{previous.date}</strong>
              </>
            )}
          </p>
        </div>
      </header>
      <div className="kpi-row">
        {METRICS.map(({ key, label, help }) => {
          const curr = latest.overall[key];
          const prev = previous?.overall[key];
          const sign = deltaSign(curr, prev);
          return (
            <div key={key} className="kpi-card" title={help}>
              <div className="kpi-label">{label}</div>
              <div className="kpi-value">{pct(curr)}</div>
              <div
                className="kpi-delta"
                style={{ color: deltaColor(sign) }}
              >
                {deltaPct(curr, prev)}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
