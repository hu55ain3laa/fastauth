import Link from "next/link";
import { GithubLogo } from "@phosphor-icons/react/dist/ssr";
import { Logo } from "./logo";
import { ThemeToggle } from "./theme-toggle";
import { MobileNav } from "./mobile-nav";
import { DocsSearch } from "./docs-search";
import { site } from "@/lib/site";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-[var(--topbar-h)] max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8">
        <Link href="/" aria-label="FastAuth home" className="text-accent">
          <Logo height={22} />
        </Link>

        <a
          href={site.links.pypi}
          target="_blank"
          rel="noopener noreferrer"
          className="chip hidden sm:inline-flex"
        >
          v{site.version}
        </a>

        <div className="ml-auto md:ml-0 md:flex-1 md:px-4">
          <DocsSearch />
        </div>

        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          <Link
            href="/docs"
            className="px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            Docs
          </Link>
          <Link
            href="/docs/quick-start"
            className="px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            Quick start
          </Link>
          <Link
            href="/docs/endpoints"
            className="px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            API
          </Link>
          <a
            href={site.links.github}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-muted transition-colors hover:text-foreground"
          >
            <GithubLogo size={16} />
            GitHub
          </a>
        </nav>

        <div className="ml-auto flex items-center gap-2 md:ml-2">
          <ThemeToggle />
          <MobileNav />
        </div>
      </div>
    </header>
  );
}
