import Link from "next/link";
import { Logo } from "./logo";
import { docsNav } from "@/lib/nav";
import { site } from "@/lib/site";

const external = [
  { href: site.links.github, label: "GitHub" },
  { href: site.links.pypi, label: "PyPI" },
  { href: site.links.issues, label: "Issues" },
  { href: site.links.ci, label: "CI" },
];

export function Footer() {
  return (
    <footer className="mt-24 border-t border-line bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-12 lg:gap-12">
          {/* Brand + authorship */}
          <div className="space-y-5 lg:col-span-4">
            <Link href="/" aria-label="FastAuth home" className="inline-block text-accent">
              <Logo height={26} />
            </Link>
            <p className="max-w-sm text-sm leading-relaxed text-muted">
              Authentication for FastAPI: JWT access and refresh tokens,
              role-based access control, and ready-made login routes, wired in
              one call.
            </p>
            <p className="text-sm leading-relaxed text-muted">
              Built by{" "}
              <a
                href={site.author.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-foreground transition-colors hover:text-accent"
              >
                {site.author.name}
              </a>
              , founder of{" "}
              <a
                href={site.company.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-foreground transition-colors hover:text-accent"
              >
                {site.company.name}
              </a>
              .
            </p>
          </div>

          {/* Documentation columns, mirroring the sidebar groups */}
          {docsNav.map((group) => (
            <div key={group.label} className="lg:col-span-2">
              <h3 className="eyebrow mb-4">{group.label}</h3>
              <ul className="space-y-2.5 text-sm">
                {group.items.map((item) => (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className="text-muted transition-colors hover:text-accent"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div className="lg:col-span-2">
            <h3 className="eyebrow mb-4">Project</h3>
            <ul className="space-y-2.5 text-sm">
              {external.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-muted transition-colors hover:text-accent"
                  >
                    {link.label}
                    <span aria-hidden>↗</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="border-t border-line">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-5 font-mono text-xs text-muted-2 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <p>
            MIT licensed · v{site.version} · tested on Python 3.10–3.14
          </p>
          <p>
            © {new Date().getFullYear()} {site.author.name} ·{" "}
            <a
              href={site.company.url}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-accent"
            >
              {site.company.name}
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
