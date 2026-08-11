"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { List, X } from "@phosphor-icons/react/dist/ssr";
import { docsNav } from "@/lib/nav";
import { site } from "@/lib/site";

export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // A drawer that scrolls the page behind it feels broken on touch.
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-expanded={open}
        className="inline-flex size-9 items-center justify-center rounded-lg border border-line text-muted transition-colors hover:border-line-strong hover:text-foreground md:hidden"
      >
        <List size={17} />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
          />
          <div className="absolute inset-y-0 right-0 flex w-[min(20rem,85vw)] flex-col border-l border-line bg-surface">
            <div className="flex h-[var(--topbar-h)] items-center justify-between border-b border-line px-4">
              <span className="eyebrow">Navigation</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="inline-flex size-9 items-center justify-center rounded-lg border border-line text-muted hover:text-foreground"
              >
                <X size={17} />
              </button>
            </div>

            <nav className="flex-1 overflow-y-auto overscroll-y-contain px-4 py-5">
              {docsNav.map((group) => (
                <div key={group.label} className="mb-6">
                  <p className="eyebrow mb-3">{group.label}</p>
                  <ul className="space-y-0.5">
                    {group.items.map((item) => {
                      const active = pathname === item.href;
                      return (
                        <li key={item.href}>
                          <Link
                            href={item.href}
                            onClick={() => setOpen(false)}
                            className={`block rounded-lg px-3 py-2 text-sm transition-colors ${
                              active
                                ? "bg-accent-soft text-accent"
                                : "text-muted hover:bg-surface-2 hover:text-foreground"
                            }`}
                          >
                            {item.label}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}

              <div className="hairline-top pt-5">
                <a
                  href={site.links.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-lg px-3 py-2 text-sm text-muted hover:text-foreground"
                >
                  GitHub ↗
                </a>
                <a
                  href={site.links.pypi}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-lg px-3 py-2 text-sm text-muted hover:text-foreground"
                >
                  PyPI ↗
                </a>
              </div>
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
