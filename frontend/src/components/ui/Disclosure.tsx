/**
 * The "everything else" container (DESIGN.md V4).
 *
 * Caveats are never deleted to reduce visual noise -- they are moved here.
 * AGENTS.md §4 is explicit that an agent optimising for a clean interface will
 * be tempted to trim them, and this component is where they go instead.
 *
 * Inline expansion rather than a drawer or modal, deliberately: the detail
 * stays spatially attached to the mark it qualifies.
 */

import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronRight } from "lucide-react";
import { useState } from "react";

export function Disclosure({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  return (
    <Collapsible.Root open={open} onOpenChange={setOpen}>
      <Collapsible.Trigger
        className="flex w-full items-center gap-2 rounded px-2 py-2 text-left text-ink-300 hover:text-ink-100"
        style={{ fontSize: "var(--t-body)" }}
      >
        <ChevronRight
          size={14}
          aria-hidden
          style={{
            transform: open ? "rotate(90deg)" : "none",
            transition: "transform 120ms",
          }}
        />
        {label}
      </Collapsible.Trigger>
      <Collapsible.Content>
        <div className="font-prose px-2 pb-2 pt-1 text-ink-200">{children}</div>
      </Collapsible.Content>
    </Collapsible.Root>
  );
}
