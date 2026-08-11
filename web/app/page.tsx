import Link from "next/link";
import type { Metadata } from "next";
import { ArrowRight, BookOpen } from "@phosphor-icons/react/dist/ssr";
import { Hero } from "@/components/landing/hero";
import { Features } from "@/components/landing/features";
import { QuickLook } from "@/components/landing/quick-look";
import { InstallCommand } from "@/components/install-command";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  title: `${site.name} · ${site.tagline}`,
  description: site.description,
  alternates: { canonical: "/" },
};

export default function Home() {
  return (
    <>
      <Hero />
      <Features />
      <QuickLook />

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 md:py-24 lg:px-8">
        <div className="panel panel-accent flex flex-col items-start gap-6 p-8 md:flex-row md:items-center md:justify-between md:p-12">
          <div>
            <h2 className="text-[clamp(1.5rem,2.6vw,2rem)] font-bold tracking-tight text-foreground">
              Stop rewriting auth
            </h2>
            <p className="mt-3 max-w-lg leading-relaxed text-muted">
              Install it, call <code className="font-mono text-accent">auth.setup(app)</code>,
              and get back to the part of your app that is actually yours.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <InstallCommand />
            <Link href="/docs" className="btn btn-primary">
              <BookOpen size={16} />
              Read the docs
              <ArrowRight size={15} weight="bold" className="btn-arrow" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
