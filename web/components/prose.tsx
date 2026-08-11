import type { ReactNode } from "react";

/**
 * The small mono label above a page title.
 * A component rather than a raw <p> because MDX wraps multi-line JSX children
 * in their own paragraph, and a <p> inside a <p> is invalid HTML.
 */
export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="eyebrow mb-3">{children}</div>;
}

/** The opening sentence of a page, set slightly larger than body copy. */
export function Lede({ children }: { children: ReactNode }) {
  return (
    <div className="lede [&>p]:my-0 [&>p+p]:mt-3">{children}</div>
  );
}
