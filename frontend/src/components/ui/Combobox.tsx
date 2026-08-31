/**
 * Searchable picker over hundreds of options.
 *
 * Radix Select offers only single-character jump, but the three pickers carry
 * 661 / 330 / 315 options with type-to-filter in the Streamlit apps, and
 * AGENTS.md §5 requires porting that behaviour exactly. cmdk supplies the part
 * that is genuinely hard to hand-roll -- aria-activedescendant, roving focus,
 * screen-reader announcements -- which is invisible when wrong.
 *
 * Items render richer than a label on purpose: project 01's list must visibly
 * mark sub-threshold players as refusable rather than hiding them, because
 * they are in the list precisely so the refusal can be shown.
 */

import * as Popover from "@radix-ui/react-popover";
import { Command } from "cmdk";
import { ChevronsUpDown } from "lucide-react";
import { useState } from "react";

export interface ComboOption {
  id: string;
  label: string;
  /** Searchable text beyond the label, e.g. club name. */
  keywords?: string;
  /** Rendered right-aligned; used for the refusal marker. */
  hint?: string;
  hintMuted?: boolean;
}

export function Combobox({
  options,
  value,
  onChange,
  placeholder,
  label,
}: {
  options: ComboOption[];
  value: string | null;
  onChange: (id: string) => void;
  placeholder: string;
  label: string;
}) {
  const [open, setOpen] = useState(false);
  const selected = options.find((o) => o.id === value);

  return (
    <div>
      <div className="label mb-1">{label}</div>
      <Popover.Root open={open} onOpenChange={setOpen}>
        <Popover.Trigger
          className="hoverable flex w-full items-center justify-between px-3 py-2 text-left"
          style={{
            background: "var(--paper-000)",
            border: "var(--rule-w) solid var(--rule-200)",
            borderRadius: "var(--radius)",
            color: selected ? "var(--ink-900)" : "var(--ink-300)",
            fontSize: "var(--t-body)",
          }}
        >
          <span className="truncate">{selected?.label ?? placeholder}</span>
          <ChevronsUpDown size={14} strokeWidth={1} aria-hidden className="shrink-0 text-ink-400" />
        </Popover.Trigger>

        <Popover.Portal>
          <Popover.Content
            align="start"
            sideOffset={4}
            className="z-50 w-[var(--radix-popover-trigger-width)] overflow-hidden"
            style={{
              background: "var(--paper-000)",
              borderRadius: "var(--radius)",
              border: "var(--rule-w) solid var(--rule-200)",
            }}
          >
            <Command
              filter={(v, search, keywords) => {
                const hay = `${v} ${keywords?.join(" ") ?? ""}`.toLowerCase();
                return hay.includes(search.toLowerCase()) ? 1 : 0;
              }}
            >
              <Command.Input
                autoFocus
                placeholder={placeholder}
                className="w-full bg-transparent px-3 py-2 outline-none"
                style={{
                  borderBottom: "var(--rule-w) solid var(--rule-200)",
                  color: "var(--ink-900)",
                  fontSize: "var(--t-body)",
                }}
              />
              <Command.List style={{ maxHeight: 300, overflowY: "auto" }}>
                <Command.Empty
                  className="px-3 py-3 text-ink-400"
                  style={{ fontSize: "var(--t-body)" }}
                >
                  No match.
                </Command.Empty>
                {options.map((o) => (
                  <Command.Item
                    key={o.id}
                    value={o.label}
                    keywords={o.keywords ? [o.keywords] : undefined}
                    onSelect={() => {
                      onChange(o.id);
                      setOpen(false);
                    }}
                    className="flex cursor-pointer items-center justify-between px-3 py-2 text-ink-200 data-[selected=true]:bg-ink-800 data-[selected=true]:text-ink-100"
                    style={{ fontSize: "var(--t-body)" }}
                  >
                    <span className="truncate">{o.label}</span>
                    {o.hint && (
                      <span
                        className="ml-3 shrink-0 font-mono"
                        style={{
                          fontSize: "var(--t-micro)",
                          color: o.hintMuted
                            ? "var(--ink-500)"
                            : "var(--ink-300)",
                        }}
                      >
                        {o.hint}
                      </span>
                    )}
                  </Command.Item>
                ))}
              </Command.List>
            </Command>
          </Popover.Content>
        </Popover.Portal>
      </Popover.Root>
    </div>
  );
}
