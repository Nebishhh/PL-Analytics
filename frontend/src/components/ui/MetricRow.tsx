/**
 * Figures in mono with tabular numerals, so columns align down the page.
 *
 * The column count is responsive rather than derived from the item count. It
 * used to be `repeat(min(items, 4), 1fr)` at every width, which at 375px put
 * four columns into a phone: the labels wrapped to two lines, and because they
 * wrapped unevenly the values no longer shared a baseline -- the one thing this
 * component exists to guarantee.
 */
export function MetricRow({
  items,
}: {
  items: { label: string; value: string; sub?: string }[];
}) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-5 md:grid-cols-4">
      {items.map((m) => (
        <div key={m.label}>
          <div className="label">{m.label}</div>
          <div
            className="font-mono text-ink-900"
            style={{ fontSize: "var(--t-figure)" }}
          >
            {m.value}
          </div>
          {m.sub && (
            <div
              className="font-mono text-ink-300"
              style={{ fontSize: "var(--t-micro)" }}
            >
              {m.sub}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
