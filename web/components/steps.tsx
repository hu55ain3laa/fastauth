import type { ReactNode } from "react";

/**
 * A numbered walkthrough. The connecting rail is drawn on the container so
 * steps stay aligned no matter how tall each one grows.
 */
export function Steps({ children }: { children: ReactNode }) {
  return (
    <div className="my-8 [counter-reset:step] space-y-8">{children}</div>
  );
}

export function Step({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="relative pl-12 [counter-increment:step] before:absolute before:left-0 before:top-0 before:flex before:size-8 before:items-center before:justify-center before:rounded-lg before:border before:border-accent-line before:bg-accent-soft before:font-mono before:text-[13px] before:font-semibold before:text-accent before:content-[counter(step)] after:absolute after:bottom-0 after:left-4 after:top-10 after:w-px after:bg-line last:after:hidden">
      <h3 className="mb-3 mt-0.5 text-lg font-semibold tracking-tight text-foreground">
        {title}
      </h3>
      <div className="[&>*:first-child]:mt-0 [&>*:last-child]:mb-0">{children}</div>
    </div>
  );
}
