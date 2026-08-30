export function Panel({
  title,
  children,
}: {
  title?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className="rounded-lg"
      style={{
        background: "var(--ink-850)",
        border: "1px solid var(--ink-700)",
        padding: "var(--s-5)",
      }}
    >
      {title && <div className="label mb-4">{title}</div>}
      {children}
    </section>
  );
}
