"use client";

import { useState, type ReactNode } from "react";

/**
 * Small tab group for showing the same step more than one way — uv or pip,
 * SQLite or Postgres — so nobody has to translate a command themselves.
 */
export function Tabs({
  labels,
  children,
}: {
  labels: string[];
  /** One child per label, in the same order. */
  children: ReactNode[];
}) {
  const [active, setActive] = useState(0);
  const panels = Array.isArray(children) ? children : [children];

  return (
    <div className="my-6">
      <div role="tablist" className="mb-2 flex gap-1">
        {labels.map((label, i) => (
          <button
            key={label}
            type="button"
            role="tab"
            aria-selected={i === active}
            onClick={() => setActive(i)}
            className={`rounded-lg px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider transition-colors ${
              i === active
                ? "bg-accent-soft text-accent"
                : "text-muted-2 hover:text-foreground"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      <div role="tabpanel" className="[&>*]:my-0">
        {panels[active]}
      </div>
    </div>
  );
}
