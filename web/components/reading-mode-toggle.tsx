"use client";

import { ArrowsIn, BookOpenText } from "@phosphor-icons/react/dist/ssr";

const STORAGE_KEY = "fastauth-reading";

/**
 * Reading mode hides the sidebar, widens the measure, and opens up the type for
 * long-form reading. Like the theme toggle, the current state lives in a class
 * on <html> and the button's appearance is decided by CSS, so it is correct on
 * first paint with no effect and no hydration mismatch.
 */
export function ReadingModeToggle() {
  function toggle() {
    const root = document.documentElement;
    const next = !root.classList.contains("reading");
    root.classList.toggle("reading", next);
    try {
      localStorage.setItem(STORAGE_KEY, next ? "on" : "off");
    } catch {
      // Storage disabled: the preference just won't persist between visits.
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle reading mode"
      title="Reading mode hides the sidebar and opens up the type"
      className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.12em] text-muted-2 transition-colors hover:border-line-strong hover:text-foreground"
    >
      <span className="when-reading-off inline-flex items-center gap-2">
        <BookOpenText size={14} />
        Reading mode
      </span>
      <span className="when-reading-on inline-flex items-center gap-2">
        <ArrowsIn size={14} />
        Exit reading mode
      </span>
    </button>
  );
}
