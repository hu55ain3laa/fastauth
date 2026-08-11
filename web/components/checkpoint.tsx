import type { ReactNode } from "react";
import { SealCheck, XCircle } from "@phosphor-icons/react/dist/ssr";

/** "Your terminal should say this" — a verifiable stopping point in a tutorial. */
export function Checkpoint({
  label = "Checkpoint",
  children,
}: {
  label?: string;
  children: ReactNode;
}) {
  return (
    <div className="my-6 overflow-hidden rounded-xl border border-accent-line bg-accent-soft/40">
      <div className="flex items-center gap-2 border-b border-accent-line px-4 py-2.5 font-mono text-[10.5px] uppercase tracking-[0.14em] text-accent">
        <SealCheck size={13} weight="fill" />
        {label}
      </div>
      <pre className="scrollbar-none overflow-x-auto px-4 py-3.5 font-mono text-[12.5px] leading-relaxed text-muted">
        {children}
      </pre>
    </div>
  );
}

export function Fixes({ children }: { children: ReactNode }) {
  return <div className="my-6 grid gap-3">{children}</div>;
}

/** One error message and the thing that makes it go away. */
export function Fix({ error, children }: { error: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface-2/50 p-4">
      <p className="flex items-start gap-2 font-mono text-[12.5px] leading-relaxed text-rose">
        <XCircle size={15} weight="fill" className="mt-0.5 shrink-0" />
        {error}
      </p>
      <div className="mt-2 pl-[23px] text-sm leading-relaxed text-muted [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
        {children}
      </div>
    </div>
  );
}
