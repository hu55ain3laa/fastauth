import type { ReactNode } from "react";
import {
  Cookie,
  Database,
  Envelope,
  Hash,
  Key,
  Path,
  Prohibit,
  RocketLaunch,
  TerminalWindow,
  UsersThree,
} from "@phosphor-icons/react/dist/ssr";
import { CodeBlock } from "@/components/code-block";

/* -------------------------------------------------------------------------
   One card anatomy, used by every card: icon + title, a line of prose, then
   an optional visual pinned to the bottom so rows line up.
   ------------------------------------------------------------------------- */

function Card({
  icon,
  title,
  children,
  visual,
  className = "",
}: {
  icon: ReactNode;
  title: string;
  children: ReactNode;
  visual?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`panel panel-hover reveal flex min-w-0 flex-col p-5 ${className}`}
    >
      <div className="mb-3 flex items-center gap-2.5">
        <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-lg border border-accent-line bg-accent-soft text-accent">
          {icon}
        </span>
        <h3 className="min-w-0 text-[0.95rem] font-semibold tracking-tight text-foreground">
          {title}
        </h3>
      </div>
      <p className="text-sm leading-relaxed text-muted">{children}</p>
      {visual && <div className="mt-4 min-w-0">{visual}</div>}
    </div>
  );
}

/**
 * The one repeated visual: a mono key with a plain-language value. Using the
 * same component for cookies, roles, and errors is what keeps the row calm.
 */
function SpecList({ rows }: { rows: { key: string; value: string }[] }) {
  return (
    <dl className="min-w-0 divide-y divide-white/[0.07] overflow-hidden rounded-xl border border-line bg-[var(--editor)]">
      {rows.map((row) => (
        <div key={row.key} className="px-3.5 py-2.5">
          <dt className="truncate font-mono text-[11.5px] text-[#6fd4c8]">{row.key}</dt>
          <dd className="mt-0.5 text-[12.5px] leading-snug text-[#8fa5a0]">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Two bars showing how the token lifetimes relate. */
function TokenLifetimes() {
  return (
    <div className="min-w-0 rounded-xl border border-line bg-[var(--editor)] p-4">
      <div className="space-y-3.5">
        <div>
          <div className="mb-1.5 flex items-baseline justify-between gap-2 font-mono text-[10.5px] uppercase tracking-[0.14em]">
            <span className="truncate text-[#6fd4c8]">access_token</span>
            <span className="shrink-0 text-[#6d837e]">30 min</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
            <div className="h-full w-[9%] rounded-full bg-[#6fd4c8]" />
          </div>
        </div>
        <div>
          <div className="mb-1.5 flex items-baseline justify-between gap-2 font-mono text-[10.5px] uppercase tracking-[0.14em]">
            <span className="truncate text-[#b3a9f2]">refresh_token</span>
            <span className="shrink-0 text-[#6d837e]">7 days</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
            <div className="h-full w-full rounded-full bg-[#b3a9f2]" />
          </div>
        </div>
      </div>
      <p className="mt-4 border-t border-white/[0.07] pt-3 font-mono text-[11px] leading-relaxed text-[#6d837e]">
        /token/refresh mints a new access token without asking for the password
        again.
      </p>
    </div>
  );
}

/* -------------------------------------------------------------------------
   Section
   ------------------------------------------------------------------------- */

export function Features() {
  return (
    <section id="features" className="border-b border-line">
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 md:py-28 lg:px-8">
        <div className="mb-12 max-w-2xl">
          <p className="eyebrow mb-4">Features</p>
          <h2 className="text-[clamp(1.9rem,3.6vw,2.75rem)] font-bold leading-tight tracking-tight text-foreground">
            Everything auth, nothing extra
          </h2>
          <p className="mt-4 text-[1.0625rem] leading-relaxed text-muted">
            FastAuth covers the auth work every FastAPI app repeats: token
            issuing, password hashing, session cookies, and role checks. Your
            code stays about your product.
          </p>
        </div>

        {/* Two wide cards carry the code, where lines have room to breathe. */}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card
            icon={<Path size={17} />}
            title="One call mounts everything"
            visual={
              <div className="space-y-3">
                <CodeBlock
                  lang="python"
                  file="main.py"
                  compact
                  code={`auth = FastAuth(engine=engine)
auth.setup(app)`}
                />
                <p className="font-mono text-[11px] leading-relaxed text-muted-2">
                  19 routes across auth, account flows, and role management, plus
                  the error handlers.
                </p>
              </div>
            }
          >
            Login, refresh, registration, logout, password reset, email
            verification, and the role API, all wired at once.
          </Card>

          <Card
            icon={<Key size={17} />}
            title="Two tokens, two lifetimes"
            visual={<TokenLifetimes />}
          >
            A short-lived access token for API calls, a long-lived refresh token
            so users are not asked to log in every half hour.
          </Card>
        </div>

        {/* Three cards sharing one visual language. */}
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <Card
            icon={<UsersThree size={17} />}
            title="Roles that read like English"
            visual={
              <SpecList
                rows={[
                  { key: "auth.roles(...)", value: "any of these roles" },
                  { key: "auth.all_roles(...)", value: "all of these roles" },
                  { key: "auth.admin", value: "the admin shortcut" },
                ]}
              />
            }
          >
            Six standard roles out of the box. Protect a single route or a whole
            router.
          </Card>

          <Card
            icon={<Cookie size={17} />}
            title="Cookies with the right flags"
            visual={
              <SpecList
                rows={[
                  { key: "HttpOnly", value: "JavaScript can never read it" },
                  { key: "Secure", value: "HTTPS only, default in production" },
                  { key: "SameSite=lax", value: "blocks cross-site sends" },
                ]}
              />
            }
          >
            An HTTP-only cookie that expires with its token. A Bearer header wins
            when both are present.
          </Card>

          <Card
            icon={<Prohibit size={17} />}
            title="Errors in one shape"
            visual={
              <SpecList
                rows={[
                  { key: "code", value: "FASTAUTH_INVALID_CREDENTIALS" },
                  { key: "message", value: "Incorrect username or password" },
                  { key: "status_code", value: "401" },
                ]}
              />
            }
          >
            Every auth failure returns the same JSON with a machine-readable
            code, so clients handle errors once.
          </Card>
        </div>

        {/* Quiet supporting facts. */}
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card icon={<Envelope size={17} />} title="Account flows">
            Password reset, change, and email verification, with delivery hooks
            for your email service.
          </Card>
          <Card icon={<RocketLaunch size={17} />} title="Production mode">
            <code className="font-mono text-accent">production=True</code>{" "}
            enforces a strong secret, secure cookies, and no default passwords.
          </Card>
          <Card icon={<TerminalWindow size={17} />} title="CLI initialization">
            <code className="font-mono text-accent">fastauth app.py</code>{" "}
            creates tables, the six standard roles, and a superadmin.
          </Card>
          <Card icon={<Database size={17} />} title="SQLModel native">
            Bring your own engine and user model. No separate auth database, no
            second source of truth.
          </Card>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Card icon={<Hash size={17} />} title="bcrypt hashing">
            Hashes with bcrypt directly, compatible with bcrypt 4 and 5, with no
            passlib dependency to keep pinned.
          </Card>
          <Card icon={<Prohibit size={17} />} title="Token revocation">
            <code className="font-mono text-accent">/logout/all</code>{" "}
            invalidates every session, and password changes do it automatically.
          </Card>
        </div>
      </div>
    </section>
  );
}
