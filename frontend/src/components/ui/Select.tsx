/**
 * Short lists only -- Position (4), Season (9). Anything longer is a Combobox,
 * because under about forty options there is nothing to search and over it
 * there is nothing else to do.
 *
 * Radix rather than a native `<select>`, decided in Step 5. A native select
 * renders its open list as operating-system chrome that cannot be typeset, and
 * in a world this committed to a printed document that is the seam where the
 * illusion breaks. The closed state was always styleable; the open one was not.
 *
 * The trade is real and worth recording: a native select gets the OS picker on
 * touch, which is genuinely better for a long list. That is exactly why the
 * long lists became Comboboxes instead of staying here.
 */

import * as RSelect from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";

export interface SelectOption {
  id: string;
  label: string;
}

export function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
}) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <RSelect.Root value={value} onValueChange={onChange}>
        <RSelect.Trigger
          className="hoverable flex w-full items-center justify-between"
          style={{
            background: "var(--paper-000)",
            border: "var(--rule-w) solid var(--rule-200)",
            borderRadius: "var(--radius)",
            color: "var(--ink-900)",
            fontSize: "var(--t-body)",
            padding: "8px 10px",
          }}
        >
          <RSelect.Value />
          <RSelect.Icon>
            {/* strokeWidth 1 so an icon reads as drawn with the same pen as the
                rules around it. Lucide's 2px round-capped default is a
                modern-UI signature that fights a hairline paper world. */}
            <ChevronDown size={14} strokeWidth={1} aria-hidden />
          </RSelect.Icon>
        </RSelect.Trigger>

        <RSelect.Portal>
          <RSelect.Content
            position="popper"
            sideOffset={4}
            className="z-50 overflow-hidden"
            style={{
              background: "var(--paper-000)",
              border: "var(--rule-w) solid var(--rule-200)",
              borderRadius: "var(--radius)",
              minWidth: "var(--radix-select-trigger-width)",
              boxShadow: "0 1px 0 var(--rule-200)",
            }}
          >
            <RSelect.Viewport style={{ padding: "3px" }}>
              {options.map((o) => (
                <RSelect.Item
                  key={o.id}
                  value={o.id}
                  className="flex cursor-default items-center justify-between outline-none"
                  style={{
                    fontSize: "var(--t-body)",
                    padding: "6px 8px",
                    borderRadius: "var(--radius)",
                    color: "var(--ink-900)",
                  }}
                >
                  <RSelect.ItemText>{o.label}</RSelect.ItemText>
                  <RSelect.ItemIndicator>
                    <Check size={13} strokeWidth={1} aria-hidden />
                  </RSelect.ItemIndicator>
                </RSelect.Item>
              ))}
            </RSelect.Viewport>
          </RSelect.Content>
        </RSelect.Portal>
      </RSelect.Root>
    </div>
  );
}
