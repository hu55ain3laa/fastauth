import Link from "next/link";
import { ArrowRight, GraduationCap } from "@phosphor-icons/react/dist/ssr";
import { CodeBlock } from "@/components/code-block";

const STEPS = [
  {
    title: "Install the package",
    body: "One dependency, plus FastAPI's standard extras for the dev server.",
    lang: "bash",
    file: "shell",
    code: `uv add fastauth_iq "fastapi[standard]"`,
  },
  {
    title: "Wire FastAuth into your app",
    body: "Point it at your engine and session. One call mounts every route and the error handlers.",
    lang: "python",
    file: "main.py",
    code: `from fastapi import FastAPI
from sqlmodel import create_engine
from fastauth import FastAuth

engine = create_engine("sqlite:///./app.db")
auth = FastAuth(secret_key="...", engine=engine, use_cookie=True)

app = FastAPI()
auth.setup(app, session_getter=get_session)`,
  },
  {
    title: "Protect your routes",
    body: "Depend on the current user, a set of roles, or the admin shortcut.",
    lang: "python",
    file: "main.py",
    code: `@app.get("/protected")
def protected(user: User = Depends(auth.current_user)):
    return {"message": f"Hello, {user.username}!"}

@app.get("/admin-only")
def admin(user: User = Depends(auth.admin)):
    return {"message": "Admins only"}`,
  },
];

export function QuickLook() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 md:py-28 lg:px-8">
        <div className="mb-12 max-w-2xl">
          <p className="eyebrow mb-4">Quick start</p>
          <h2 className="text-[clamp(1.9rem,3.6vw,2.75rem)] font-bold leading-tight tracking-tight text-foreground">
            A working auth system in three steps
          </h2>
          <p className="mt-4 text-[1.0625rem] leading-relaxed text-muted">
            Login, refresh tokens, registration, roles, and protected routes.
            Run{" "}
            <code className="font-mono text-accent">uv run fastapi dev main.py</code>{" "}
            and every endpoint is in{" "}
            <code className="font-mono text-accent">/docs</code>, documented and
            ready to try.
          </p>
        </div>

        {/* Stacked rather than three columns: Python needs the horizontal room,
            and equal-width columns forced either clipping or uneven cards. */}
        <div className="space-y-4">
          {STEPS.map((step, index) => (
            <div
              key={step.title}
              className="panel reveal grid min-w-0 gap-5 p-5 md:grid-cols-[minmax(0,18rem)_minmax(0,1fr)] md:items-start md:gap-8 md:p-6"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <span className="inline-flex size-7 shrink-0 items-center justify-center rounded-lg border border-accent-line bg-accent-soft font-mono text-[12px] font-semibold text-accent">
                    {index + 1}
                  </span>
                  <h3 className="text-[0.95rem] font-semibold tracking-tight text-foreground">
                    {step.title}
                  </h3>
                </div>
                <p className="mt-2.5 text-sm leading-relaxed text-muted md:pl-10">
                  {step.body}
                </p>
              </div>

              <div className="min-w-0">
                <CodeBlock
                  lang={step.lang}
                  file={step.file}
                  code={step.code}
                  compact
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-3">
          <Link href="/docs/quick-start" className="btn btn-primary">
            Read the quick start
            <ArrowRight size={15} weight="bold" className="btn-arrow" />
          </Link>
          <Link href="/docs/easy-mode" className="btn btn-secondary">
            <GraduationCap size={16} />
            New to FastAPI? Try easy mode
          </Link>
        </div>
      </div>
    </section>
  );
}
