import Link from "next/link";
import { ArrowRight, GithubLogo } from "@phosphor-icons/react/dist/ssr";
import { JwtDecoder } from "@/components/jwt-decoder";
import { InstallCommand } from "@/components/install-command";
import { site } from "@/lib/site";

export function Hero() {
  return (
    <section className="hero-section border-b border-line">
      <div className="hero-grid" aria-hidden />
      <div className="hero-glow" aria-hidden />

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:px-8">
        <div>
          <span className="hero-eyebrow nb-rise nb-rise-1">
            <span className="hero-pulse" aria-hidden />
            Authentication for FastAPI
          </span>

          <h1 className="hero-h1 nb-rise nb-rise-2 mt-7">
            Login, tokens,
            <br />
            and roles.
            <br />
            Wired in <span className="hero-h1-accent">one call</span>.
          </h1>

          <p className="nb-rise nb-rise-3 mt-6 max-w-xl text-[1.0625rem] leading-relaxed text-muted">
            FastAuth adds JWT access and refresh tokens, role-based access
            control, and ready-made login routes to any FastAPI + SQLModel app.
            Call <code className="font-mono text-accent">auth.setup(app)</code>{" "}
            and start protecting routes.
          </p>

          <div className="nb-rise nb-rise-4 mt-8 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <Link href="/docs/quick-start" className="btn btn-primary">
                Get started
                <ArrowRight size={15} weight="bold" className="btn-arrow" />
              </Link>
              <a
                href={site.links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                <GithubLogo size={16} />
                GitHub
              </a>
            </div>
            <InstallCommand className="flex max-w-md" />
          </div>

          <p className="nb-rise nb-rise-5 mt-7 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-2">
            v{site.version} · MIT ·{" "}
            <a
              href={site.links.ci}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-accent"
            >
              tested on Python 3.10–3.14
            </a>
          </p>
        </div>

        <div className="nb-rise nb-rise-3 lg:pl-4">
          <JwtDecoder />
        </div>
      </div>
    </section>
  );
}
