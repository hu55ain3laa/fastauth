import Link from "next/link";
import { ArrowRight } from "@phosphor-icons/react/dist/ssr";
import { docsNav } from "@/lib/nav";

/** The full documentation outline as cards. Used on the docs landing page. */
export function DocIndex() {
  return (
    <div className="my-8 space-y-10 not-prose">
      {docsNav.map((group) => (
        <div key={group.label}>
          <p className="eyebrow mb-4">{group.label}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {group.items
              .filter((item) => item.href !== "/docs")
              .map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="panel panel-hover group p-4"
                >
                  <span className="flex items-center gap-1.5 font-semibold text-foreground group-hover:text-accent">
                    {item.label}
                    <ArrowRight
                      size={13}
                      weight="bold"
                      className="opacity-0 transition-opacity group-hover:opacity-100"
                    />
                  </span>
                  <span className="mt-1 block text-sm leading-relaxed text-muted">
                    {item.summary}
                  </span>
                </Link>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
