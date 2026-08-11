"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft, ArrowRight } from "@phosphor-icons/react/dist/ssr";
import { docNeighbours } from "@/lib/nav";

export function DocPager() {
  const pathname = usePathname();
  const { prev, next } = docNeighbours(pathname);

  if (!prev && !next) return null;

  return (
    <nav
      aria-label="Documentation pages"
      className="mt-16 grid gap-3 border-t border-line pt-8 sm:grid-cols-2"
    >
      {prev ? (
        <Link
          href={prev.href}
          className="panel panel-hover group flex flex-col gap-1 p-4"
        >
          <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-2">
            <ArrowLeft size={11} weight="bold" />
            Previous
          </span>
          <span className="font-semibold text-foreground group-hover:text-accent">
            {prev.label}
          </span>
        </Link>
      ) : (
        <span />
      )}

      {next && (
        <Link
          href={next.href}
          className="panel panel-hover group flex flex-col items-end gap-1 p-4 text-right sm:col-start-2"
        >
          <span className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-2">
            Next
            <ArrowRight size={11} weight="bold" />
          </span>
          <span className="font-semibold text-foreground group-hover:text-accent">
            {next.label}
          </span>
        </Link>
      )}
    </nav>
  );
}
