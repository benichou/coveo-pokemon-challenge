import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";
import type { EvalRunWithMeta, LayerStats } from "../schemas";

type SeriesPoint = {
  date: string;
  accuracy: number;
  precision: number;
  hard_recall: number;
  citation_precision: number;
};

function toSeries(
  runs: EvalRunWithMeta[],
  pick: (r: EvalRunWithMeta) => LayerStats,
): SeriesPoint[] {
  return runs.map((r) => {
    const s = pick(r);
    return {
      date: r.date,
      accuracy: round(s.accuracy),
      precision: round(s.precision),
      hard_recall: round(s.hard_recall),
      citation_precision: round(s.citation_precision),
    };
  });
}

function round(x: number): number {
  return Math.round(x * 1000) / 1000;
}

const LINES = [
  { key: "accuracy", label: "Accuracy", color: "#2563eb" },
  { key: "precision", label: "Precision", color: "#16a34a" },
  { key: "hard_recall", label: "Hard recall", color: "#f59e0b" },
  { key: "citation_precision", label: "Citation precision", color: "#a855f7" },
] as const;

function Chart({
  title,
  subtitle,
  data,
}: {
  title: string;
  subtitle?: string;
  data: SeriesPoint[];
}) {
  return (
    <div className="chart-card">
      <h3>{title}</h3>
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart
            data={data}
            margin={{ top: 8, right: 16, bottom: 8, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis
              domain={[0, 1]}
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
              tick={{ fontSize: 12 }}
            />
            <Tooltip
              formatter={(v) =>
                typeof v === "number" ? `${(v * 100).toFixed(1)}%` : String(v)
              }
              labelStyle={{ fontWeight: 600 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {LINES.map((l) => (
              <Line
                key={l.key}
                type="monotone"
                dataKey={l.key}
                name={l.label}
                stroke={l.color}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type Props = {
  runs: EvalRunWithMeta[];
};

export function TimeSeries({ runs }: Props) {
  return (
    <section className="time-series">
      <h2>Quality over time</h2>
      <Chart
        title="Overall"
        subtitle="All 100 golden questions per run"
        data={toSeries(runs, (r) => r.overall)}
      />
      <div className="chart-grid">
        <Chart
          title="Layer 1 — single-fact"
          subtitle="50 questions · type/gen/ability/stat lookups"
          data={toSeries(runs, (r) => r.by_layer["1"])}
        />
        <Chart
          title="Layer 2 — multi-doc synthesis"
          subtitle="35 questions · the SE-aided sweet spot"
          data={toSeries(runs, (r) => r.by_layer["2"])}
        />
        <Chart
          title="Layer 3 — refusal / edge"
          subtitle="15 questions · RGA should refuse or stay nuanced"
          data={toSeries(runs, (r) => r.by_layer["3"])}
        />
      </div>
    </section>
  );
}
