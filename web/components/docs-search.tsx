"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { MagnifyingGlass } from "@phosphor-icons/react/dist/ssr";

type Record_ = {
  href: string;
  page: string;
  heading: string | null;
  text: string;
};

/** Every query term must appear somewhere; matches in the heading rank higher. */
function score(record: Record_, terms: string[]) {
  const heading = (record.heading ?? record.page).toLowerCase();
  const page = record.page.toLowerCase();
  const text = record.text.toLowerCase();
  let total = 0;

  for (const term of terms) {
    const inHeading = heading.includes(term);
    const inPage = page.includes(term);
    const inText = text.includes(term);
    if (!inHeading && !inPage && !inText) return 0;
    if (inHeading) total += 10;
    if (inPage) total += 4;
    if (inText) total += 1;
  }
  return total;
}

/** A short window of the text around the first match, for context. */
function snippet(text: string, term: string) {
  const at = text.toLowerCase().indexOf(term);
  if (at === -1) return text.slice(0, 120);
  const start = Math.max(0, at - 40);
  return (start > 0 ? "…" : "") + text.slice(start, start + 130);
}

export function DocsSearch() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [records, setRecords] = useState<Record_[] | null>(null);
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // The index is only worth fetching once someone actually searches.
  const load = useCallback(() => {
    if (records) return;
    fetch("/search-index.json")
      .then((r) => r.json())
      .then(setRecords)
      .catch(() => setRecords([]));
  }, [records]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const typing =
        target?.tagName === "INPUT" || target?.tagName === "TEXTAREA";

      if ((event.metaKey || event.ctrlKey) && event.key === "k") {
        event.preventDefault();
        setOpen((v) => !v);
      } else if (event.key === "/" && !typing && !open) {
        event.preventDefault();
        setOpen(true);
      } else if (event.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (open) {
      load();
      inputRef.current?.focus();
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open, load]);

  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const results = terms.length
    ? (records ?? [])
        .map((record) => ({ record, s: score(record, terms) }))
        .filter((r) => r.s > 0)
        .sort((a, b) => b.s - a.s)
        .slice(0, 8)
        .map((r) => r.record)
    : [];

  function go(record: Record_) {
    setOpen(false);
    setQuery("");
    router.push(record.href);
  }

  function onInputKey(event: React.KeyboardEvent) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter" && results[active]) {
      event.preventDefault();
      go(results[active]);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg border border-line px-2.5 py-1.5 text-sm text-muted-2 transition-colors hover:border-line-strong hover:text-foreground sm:w-52 sm:justify-between"
        aria-label="Search documentation"
      >
        <span className="inline-flex items-center gap-2">
          <MagnifyingGlass size={15} />
          <span className="hidden sm:inline">Search docs</span>
        </span>
        <kbd className="hidden rounded border border-line px-1.5 py-0.5 font-mono text-[10px] sm:inline">
          ⌘K
        </kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh]">
          <button
            type="button"
            aria-label="Close search"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
          />

          <div
            role="dialog"
            aria-modal="true"
            aria-label="Search documentation"
            className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-line-strong bg-surface shadow-2xl"
          >
            <div className="flex items-center gap-3 border-b border-line px-4">
              <MagnifyingGlass size={17} className="shrink-0 text-muted-2" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setActive(0);
                }}
                onKeyDown={onInputKey}
                placeholder="Search the documentation…"
                className="w-full bg-transparent py-3.5 text-[0.95rem] text-foreground outline-none placeholder:text-muted-2"
              />
              <kbd className="shrink-0 rounded border border-line px-1.5 py-0.5 font-mono text-[10px] text-muted-2">
                esc
              </kbd>
            </div>

            <div className="max-h-[55vh] overflow-y-auto overscroll-contain p-2">
              {terms.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-muted-2">
                  Search across every documentation page.
                </p>
              )}

              {terms.length > 0 && results.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-muted-2">
                  {records === null
                    ? "Loading…"
                    : `No matches for "${query}".`}
                </p>
              )}

              {results.map((record, i) => (
                <button
                  key={record.href + i}
                  type="button"
                  onClick={() => go(record)}
                  onMouseEnter={() => setActive(i)}
                  className={`block w-full rounded-lg px-3 py-2.5 text-left transition-colors ${
                    i === active ? "bg-accent-soft" : "hover:bg-surface-2"
                  }`}
                >
                  <span className="flex items-baseline gap-2">
                    <span
                      className={`text-sm font-medium ${
                        i === active ? "text-accent" : "text-foreground"
                      }`}
                    >
                      {record.heading ?? record.page}
                    </span>
                    {record.heading && (
                      <span className="font-mono text-[10px] uppercase tracking-wider text-muted-2">
                        {record.page}
                      </span>
                    )}
                  </span>
                  <span className="mt-0.5 block truncate text-xs text-muted">
                    {snippet(record.text, terms[0])}
                  </span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-4 border-t border-line px-4 py-2 font-mono text-[10px] uppercase tracking-wider text-muted-2">
              <span>↑↓ navigate</span>
              <span>↵ open</span>
              <span>esc close</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
