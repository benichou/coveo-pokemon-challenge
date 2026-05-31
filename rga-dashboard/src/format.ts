export function pct(x: number): string {
  return `${(x * 100).toFixed(1)}%`;
}

export function deltaPct(curr: number, prev: number | undefined): string {
  if (prev === undefined) return "—";
  const d = (curr - prev) * 100;
  const sign = d > 0 ? "+" : "";
  return `${sign}${d.toFixed(1)} pts`;
}

export function deltaSign(curr: number, prev: number | undefined): -1 | 0 | 1 {
  if (prev === undefined) return 0;
  const d = curr - prev;
  if (Math.abs(d) < 0.005) return 0;
  return d > 0 ? 1 : -1;
}
