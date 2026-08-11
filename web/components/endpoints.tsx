import type { ReactNode } from "react";
import { LockSimple } from "@phosphor-icons/react/dist/ssr";

type Method = "GET" | "POST" | "PUT" | "DELETE";

export function EndpointList({ children }: { children: ReactNode }) {
  return (
    <div className="my-6 overflow-hidden rounded-xl border border-line">
      {children}
    </div>
  );
}

export function Endpoint({
  method,
  path,
  admin = false,
  children,
}: {
  method: Method;
  path: string;
  /** Marks routes that require an admin role. */
  admin?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="grid grid-cols-[auto_1fr] items-start gap-x-3 gap-y-1.5 border-b border-line p-3.5 transition-colors last:border-b-0 hover:bg-surface-2/60 md:grid-cols-[5rem_minmax(0,18rem)_1fr] md:items-center md:gap-x-4">
      <span className={`method method-${method.toLowerCase()}`}>{method}</span>

      <span className="flex min-w-0 flex-wrap items-center gap-2">
        <code className="code-plain font-mono text-[0.8125rem] text-foreground">
          {path}
        </code>
        {admin && (
          <span className="inline-flex items-center gap-1 rounded-md border border-line px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-2">
            <LockSimple size={10} weight="bold" />
            admin
          </span>
        )}
      </span>

      <span className="col-span-2 text-sm leading-relaxed text-muted md:col-span-1">
        {children}
      </span>
    </div>
  );
}
