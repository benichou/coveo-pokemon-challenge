// Phase 6F.7c — prompt-history section with expandable diffs.
//
// One card per prompt version (newest first). Each card:
//   - shows version, date, applied_by, rationale, expected lift, and a
//     "Live now" badge on the currently-deployed version
//   - has a stable anchor id matching the time-series chart marker so the
//     marker's click handler can scroll-to this card
//   - has a collapsible diff (using the `diff` package's diffLines) that
//     compares the version's prompt text against its predecessor's
//
// We render the diff ourselves rather than pulling in a full diff-viewer
// UI library; the dashboard bundle is already heavy from recharts.

import { diffLines } from "diff";
import { pairWithPrevious } from "../loadPromptHistory";
import type { PromptVersion } from "../schemas";

function makeAnchorId(version: string, filename: string): string {
  // Keep this in sync with loadPromptHistory.makeAnchorId — duplication is
  // intentional to keep the function pure / not exported from the loader.
  const slug = `${version}-${filename.replace(/\.yaml$/, "")}`;
  return `prompt-${slug.replace(/[^a-zA-Z0-9-]+/g, "-")}`;
}

function formatPercent(v: number | undefined): string {
  if (v === undefined || v === null) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

function countDiffChanges(
  current: PromptVersion,
  previous: PromptVersion | null,
): { added: number; removed: number } {
  if (previous == null) return { added: 0, removed: 0 };
  const parts = diffLines(previous.prompt, current.prompt);
  let added = 0;
  let removed = 0;
  for (const part of parts) {
    // `count` is the number of lines in this hunk; we want the change-only
    // ones (added or removed parts). Unchanged hunks have neither flag.
    const lines = part.count ?? part.value.split("\n").length - 1;
    if (part.added) added += lines;
    else if (part.removed) removed += lines;
  }
  return { added, removed };
}

function DiffView({
  current,
  previous,
}: {
  current: PromptVersion;
  previous: PromptVersion;
}) {
  // Line-level diff is the right granularity for prompts — they're naturally
  // line-structured (numbered rules, paragraphs), and word-diff inside a
  // line tends to be visually noisy.
  const parts = diffLines(previous.prompt, current.prompt);
  return (
    <pre className="diff">
      {parts.map((part, idx) => {
        const cls = part.added
          ? "diff-added"
          : part.removed
            ? "diff-removed"
            : "diff-unchanged";
        const prefix = part.added ? "+ " : part.removed ? "- " : "  ";
        // Split into lines so each gets its own prefix/background; trailing
        // empty splits from \n at end of string are dropped.
        const lines = part.value.split("\n");
        if (lines[lines.length - 1] === "") lines.pop();
        return (
          <span key={idx} className={cls}>
            {lines.map((line, i) => (
              <span key={i} className="diff-line">
                <span className="diff-prefix">{prefix}</span>
                {line}
                {"\n"}
              </span>
            ))}
          </span>
        );
      })}
    </pre>
  );
}

function PromptCard({
  current,
  previous,
}: {
  current: PromptVersion;
  previous: PromptVersion | null;
}) {
  const anchorId = makeAnchorId(current.version, current.filename);
  const { added, removed } = countDiffChanges(current, previous);
  const liftEntries = Object.entries(current.expected_lift);

  return (
    <article
      id={anchorId}
      className={`prompt-card${current.is_current ? " prompt-card--live" : ""}`}
    >
      <header className="prompt-card-header">
        <div className="prompt-card-title">
          <h3>
            v{current.version}
            {current.is_current && (
              <span className="prompt-live-badge">Live now</span>
            )}
          </h3>
          <p className="prompt-card-meta">
            Applied {current.applied_date} by{" "}
            <code>{current.applied_by}</code>
            {previous && (
              <>
                {" · "}
                <span className="diff-count">
                  <span className="diff-count-added">+{added}</span>{" "}
                  <span className="diff-count-removed">−{removed}</span> lines
                  vs v{previous.version}
                </span>
              </>
            )}
          </p>
        </div>
        <a className="prompt-card-anchor" href={`#${anchorId}`} aria-label="Direct link to this version">
          #
        </a>
      </header>

      <section className="prompt-rationale">
        <h4>Rationale</h4>
        <pre>{current.rationale}</pre>
      </section>

      {liftEntries.length > 0 && (
        <section className="prompt-lift">
          <h4>Predicted lift at apply time</h4>
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>From</th>
                <th>Target</th>
                <th>Δ</th>
              </tr>
            </thead>
            <tbody>
              {liftEntries.map(([metric, lift]) => {
                const from = lift.from ?? lift.from_;
                const delta =
                  from !== undefined ? lift.target - from : undefined;
                return (
                  <tr key={metric}>
                    <td>{metric}</td>
                    <td>{formatPercent(from)}</td>
                    <td>{formatPercent(lift.target)}</td>
                    <td>
                      {delta !== undefined
                        ? `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(
                            0,
                          )}pts`
                        : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {current.validated_against && (
            <p className="prompt-validated">
              Measured against{" "}
              <code>{current.validated_against}</code>
            </p>
          )}
        </section>
      )}

      {previous && (
        <details className="prompt-diff">
          <summary>
            Show diff vs v{previous.version} ({added} added, {removed}{" "}
            removed)
          </summary>
          <DiffView current={current} previous={previous} />
        </details>
      )}

      {!previous && (
        <p className="prompt-baseline-note">
          Baseline version — no predecessor to diff against.
        </p>
      )}
    </article>
  );
}

export function PromptHistory() {
  const pairs = pairWithPrevious();
  if (pairs.length === 0) {
    // Shouldn't happen — pokemon-rga.yaml always exists — but render
    // defensively rather than blowing up.
    return null;
  }
  return (
    <section className="prompt-history">
      <h2>Prompt history</h2>
      <p className="section-subtitle">
        Every version of the RGA Custom Prompt that has been live on the model,
        newest first. Each entry is the result of the closed-loop analyzer
        proposing a change → guardrails passing → the apply script PUTting it
        to Coveo's ML Models API. Click a chart marker above to jump to a
        specific version.
      </p>
      {pairs.map(({ current, previous }) => (
        <PromptCard
          key={current.filename}
          current={current}
          previous={previous}
        />
      ))}
    </section>
  );
}
