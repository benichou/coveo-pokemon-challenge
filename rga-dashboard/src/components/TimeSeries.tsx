import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";
import type {
  EvalRunWithMeta,
  LayerStats,
  PromptChangeEvent,
} from "../schemas";

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

function handleMarkerClick(anchorId: string) {
  // Smooth-scroll the corresponding card in the prompt-history section into
  // view. The anchor element is rendered by PromptHistory; we use a hash
  // navigation so the URL also updates, useful for sharing direct links.
  const el = document.getElementById(anchorId);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
    el.classList.add("flash");
    window.setTimeout(() => el.classList.remove("flash"), 1500);
  }
  if (typeof window !== "undefined") {
    window.history.replaceState(null, "", `#${anchorId}`);
  }
}

// Vertical reference line on the chart for every prompt change. Color matches
// the "applied" semantic across the dashboard. The label sits above the line
// and is click-to-scroll-to-history-entry.
function PromptMarkers({ events }: { events: PromptChangeEvent[] }) {
  return (
    <>
      {events.map((evt) => (
        <ReferenceLine
          key={evt.anchor_id}
          x={evt.applied_date}
          stroke="#0ea5e9"
          strokeDasharray="4 3"
          strokeWidth={1.5}
        >
          <Label
            value={`v${evt.version}`}
            position="top"
            fill="#0ea5e9"
            fontSize={11}
            fontWeight={600}
            style={{ cursor: "pointer" }}
            onClick={() => handleMarkerClick(evt.anchor_id)}
          />
        </ReferenceLine>
      ))}
    </>
  );
}

function Chart({
  title,
  subtitle,
  data,
  promptEvents,
}: {
  title: string;
  subtitle?: string;
  data: SeriesPoint[];
  promptEvents?: PromptChangeEvent[];
}) {
  // Only show markers that fall inside the current chart's x-domain (the
  // dates that actually appear in `data`). Prompt-changes from before the
  // earliest eval run can't be positioned meaningfully on a date-string axis.
  const xDates = new Set(data.map((d) => d.date));
  const inRange = (promptEvents ?? []).filter((e) =>
    xDates.has(e.applied_date),
  );

  return (
    <div className="chart-card">
      <h3>{title}</h3>
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      <div className="chart-canvas">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart
            data={data}
            margin={{ top: 24, right: 16, bottom: 8, left: 0 }}
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
            <PromptMarkers events={inRange} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type Props = {
  runs: EvalRunWithMeta[];
  promptEvents?: PromptChangeEvent[];
};

export function TimeSeries({ runs, promptEvents }: Props) {
  return (
    <section className="time-series">
      <h2>Quality over time</h2>
      {promptEvents && promptEvents.length > 0 && (
        <p className="chart-legend-note">
          <span
            className="prompt-marker-dot"
            aria-hidden
            style={{ background: "#0ea5e9" }}
          />
          Dashed vertical lines mark dates the closed loop applied a new RGA
          prompt version. Click a label to jump to the version's diff.
        </p>
      )}
      <Chart
        title="Overall"
        subtitle="All 100 golden questions per run"
        data={toSeries(runs, (r) => r.overall)}
        promptEvents={promptEvents}
      />
      <div className="chart-grid">
        <Chart
          title="Layer 1 — single-fact"
          subtitle="50 questions · type/gen/ability/stat lookups"
          data={toSeries(runs, (r) => r.by_layer["1"])}
          promptEvents={promptEvents}
        />
        <Chart
          title="Layer 2 — multi-doc synthesis"
          subtitle="35 questions · the SE-aided sweet spot"
          data={toSeries(runs, (r) => r.by_layer["2"])}
          promptEvents={promptEvents}
        />
        <Chart
          title="Layer 3 — refusal / edge"
          subtitle="15 questions · RGA should refuse or stay nuanced"
          data={toSeries(runs, (r) => r.by_layer["3"])}
          promptEvents={promptEvents}
        />
      </div>
    </section>
  );
}
