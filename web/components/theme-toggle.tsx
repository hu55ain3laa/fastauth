"use client";

import { Moon, Sun } from "@phosphor-icons/react/dist/ssr";

const STORAGE_KEY = "fastauth-theme";

/**
 * Which icon shows is decided by CSS from the class on <html>, not by React
 * state. That keeps the button correct on first paint (the inline script in the
 * layout has already set the class) with no effect and no hydration mismatch.
 */
export function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const next = root.classList.contains("light") ? "dark" : "light";
    root.classList.toggle("dark", next === "dark");
    root.classList.toggle("light", next === "light");
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Private browsing with storage disabled: the theme just won't persist.
    }
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle color theme"
      className="inline-flex size-9 items-center justify-center rounded-lg border border-line text-muted transition-colors hover:border-line-strong hover:text-foreground"
    >
      <Sun size={17} className="hidden dark:block" />
      <Moon size={17} className="block dark:hidden" />
    </button>
  );
}
