/**
 * The system's one container.
 *
 * `tone` distinguishes the two things a panel can be, which previously looked
 * identical: the CONTROLS a reader operates, and the RESULT those controls
 * produced. Rendering both as the same raised card made every screen read as
 * one long stacked form. Controls now recede into the page ground; the result
 * sits above it and carries a hairline of the active tool's accent along its
 * top edge -- wayfinding, on chrome, nowhere near a mark (V1).
 */
export function Panel({
  title,
  tone = "raised",
  animate = false,
  children,
}: {
  title?: string;
  tone?: "raised" | "recessed" | "result";
  animate?: boolean;
  children: React.ReactNode;
}) {
  const ground = tone === "recessed" ? "var(--ink-900)" : "var(--ink-850)";
  return (
    <section
      className={`rounded-lg${animate ? " panel-in" : ""}`}
      style={{
        background: ground,
        border: "1px solid var(--ink-700)",
        borderTop:
          tone === "result"
            ? "2px solid var(--accent)"
            : "1px solid var(--ink-700)",
        padding: "var(--s-5)",
      }}
    >
      {title && <div className="label mb-4">{title}</div>}
      {children}
    </section>
  );
}
