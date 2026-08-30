/** Figures in mono with tabular numerals, so columns align down the page. */
export function MetricRow({
  items,
}: {
  items: { label: string; value: string; sub?: string }[];
}) {
  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${Math.min(items.length, 4)}, minmax(0, 1fr))` }}>
      {items.map((m) => (
        <div key={m.label}>
          <div className="label">{m.label}</div>
          <div
            className="font-mono text-ink-100"
            style={{ fontSize: "var(--t-figure)" }}
          >
            {m.value}
          </div>
          {m.sub && (
            <div className="font-mono text-ink-400" style={{ fontSize: "var(--t-micro)" }}>
              {m.sub}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
