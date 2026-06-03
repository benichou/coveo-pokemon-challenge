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
  PromptChangeDayMarker,
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

// Vertical reference line on the chart, one per *date* on which a prompt
// change happened. Multiple changes on the same date collapse into one
// marker — the loader's day-grouping logic owns the label format. Click
// scrolls to the LAST version applied that day (most relevant card).
function PromptMarkers({ markers }: { markers: PromptChangeDayMarker[] }) {
  return (
    <>
      {markers.map((m) => (
        <ReferenceLine
          key={m.applied_date}
          x={m.applied_date}
          stroke="#0ea5e9"
          strokeDasharray="4 3"
          strokeWidth={1.5}
        >
          <Label
            value={m.label}
            position="top"
            fill="#0ea5e9"
            fontSize={11}
            fontWeight={600}
            style={{ cursor: "pointer" }}
            onClick={() => handleMarkerClick(m.click_anchor_id)}
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
  promptMarkers,
}: {
  title: string;
  subtitle?: string;
  data: SeriesPoint[];
  promptMarkers?: PromptChangeDayMarker[];
}) {
  // Only show markers that fall inside the current chart's x-domain (the
  // dates that actually appear in `data`). Prompt-changes from before the
  // earliest eval run can't be positioned meaningfully on a date-string axis.
  const xDates = new Set(data.map((d) => d.date));
  const inRange = (promptMarkers ?? []).filter((m) =>
    xDates.has(m.applied_date),
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
            <PromptMarkers markers={inRange} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type Props = {
  runs: EvalRunWithMeta[];
  promptMarkers?: PromptChangeDayMarker[];
};

export function TimeSeries({ runs, promptMarkers }: Props) {
  return (
    <section className="time-series">
      <h2>Quality over time</h2>
      {promptMarkers && promptMarkers.length > 0 && (
        <p className="chart-legend-note">
          <span
            className="prompt-marker-dot"
            aria-hidden
            style={{ background: "#0ea5e9" }}
          />
          Dashed vertical lines mark dates a new RGA prompt version was
          applied. Days with multiple applies are collapsed into one marker
          (e.g. <code>v1.0.0 → v1.1.0</code>). Click a label to jump to the
          version's diff.
        </p>
      )}
      <Chart
        title="Overall"
        subtitle="All 100 golden questions per run"
        data={toSeries(runs, (r) => r.overall)}
        promptMarkers={promptMarkers}
      />
      <div className="chart-grid">
        <Chart
          title="Layer 1 — single-fact"
          subtitle="50 questions · type/gen/ability/stat lookups"
          data={toSeries(runs, (r) => r.by_layer["1"])}
          promptMarkers={promptMarkers}
        />
        <Chart
          title="Layer 2 — multi-doc synthesis"
          subtitle="35 questions · the SE-aided sweet spot"
          data={toSeries(runs, (r) => r.by_layer["2"])}
          promptMarkers={promptMarkers}
        />
        <Chart
          title="Layer 3 — refusal / edge"
          subtitle="15 questions · RGA should refuse or stay nuanced"
          data={toSeries(runs, (r) => r.by_layer["3"])}
          promptMarkers={promptMarkers}
        />
      </div>
    </section>
  );
}
