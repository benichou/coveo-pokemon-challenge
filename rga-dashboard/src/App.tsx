import "./App.css";
import { runs, latestRun, previousRun } from "./loadRuns";
import { promptChangeEvents } from "./loadPromptHistory";
import { SummaryCard } from "./components/SummaryCard";
import { TimeSeries } from "./components/TimeSeries";
import { CategoryBreakdown } from "./components/CategoryBreakdown";
import { FailuresTable } from "./components/FailuresTable";
import { PromptHistory } from "./components/PromptHistory";

function EmptyState() {
  return (
    <div className="empty">
      <h1>No eval runs yet</h1>
      <p>
        Run the evaluator from <code>rga-eval/</code>:{" "}
        <code>uv run python src/main.py</code>
      </p>
      <p className="muted">
        The dashboard reads <code>eval-runs/*-full.json</code> at build time.
        Smoke and layer-scan runs are intentionally excluded.
      </p>
    </div>
  );
}

function App() {
  if (!latestRun) {
    return (
      <main className="app">
        <Header />
        <EmptyState />
      </main>
    );
  }
  return (
    <main className="app">
      <Header />
      <SummaryCard latest={latestRun} previous={previousRun} />
      <TimeSeries runs={runs} promptEvents={promptChangeEvents} />
      <PromptHistory />
      <CategoryBreakdown run={latestRun} />
      <FailuresTable run={latestRun} />
      <Footer />
    </main>
  );
}

function Header() {
  return (
    <header className="app-header">
      <div className="title">
        <h1>RGA Skill Evaluator</h1>
        <p className="tagline">
          Daily quality scorecard for Coveo's RGA on the Pokemon index
        </p>
      </div>
      <div className="links">
        <a
          href="https://github.com/benichou/coveo-pokemon-challenge"
          target="_blank"
          rel="noreferrer"
        >
          GitHub ↗
        </a>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="app-footer">
      <p>
        Generated daily at 06:00 UTC by GitHub Actions · LLM judge ={" "}
        <code>claude-sonnet-4-5-20250929</code> · Golden dataset = 100 questions
        (50/35/15 split across layers)
      </p>
      <p className="muted">
        Hard recall is deterministic (substring match on expected facts).
        Accuracy and precision are LLM-judged via Anthropic tool-use forcing.
      </p>
    </footer>
  );
}

export default App;
