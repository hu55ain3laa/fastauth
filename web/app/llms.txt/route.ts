import { docsNav } from "@/lib/nav";
import { site } from "@/lib/site";

/**
 * The llms.txt convention: a curated map of the docs for AI coding agents.
 * A large share of documentation traffic now comes from agents rather than
 * browsers, and a developer's first contact with FastAuth is increasingly
 * "add auth to my FastAPI app" typed into one. This is what that agent reads.
 */
export const dynamic = "force-static";

export function GET() {
  const sections = docsNav
    .map((group) => {
      const items = group.items
        .map((item) => `- [${item.label}](${site.url}${item.href}): ${item.summary}`)
        .join("\n");
      return `## ${group.label}\n\n${items}`;
    })
    .join("\n\n");

  const body = `# ${site.name}

> ${site.description} Install with \`uv add ${site.package}\`, then call \`auth.setup(app)\`.

FastAuth is a Python library for FastAPI applications using SQLModel. It works
with an existing engine and user model rather than owning the database.

Minimal working setup:

\`\`\`python
from fastapi import FastAPI, Depends
from sqlmodel import create_engine
from fastauth import FastAuth, User

engine = create_engine("sqlite:///./app.db")
auth = FastAuth(secret_key="...", engine=engine)

app = FastAPI()
auth.setup(app)

@app.get("/protected")
def protected(user: User = Depends(auth.current_user)):
    return {"hello": user.username}
\`\`\`

Key facts an agent should not get wrong:

- The package on PyPI is \`${site.package}\`; the import is \`fastauth\`.
- \`auth.setup(app)\` mounts all routes and error handlers. Do not mount routers
  by hand unless deliberately customising.
- Route protection uses FastAPI dependencies: \`auth.current_user\`,
  \`auth.roles("admin")\`, \`auth.all_roles("a", "b")\`, \`auth.admin\`,
  \`auth.verified_user\`. Use \`auth.required\` for a whole router.
- Requires Python 3.10+. Current version ${site.version}. MIT licensed.
- In production set \`production=True\` (or \`FASTAUTH_PRODUCTION=1\`) and provide
  a \`SECRET_KEY\` of 32+ characters. It will refuse to start otherwise.
- Tokens are JWTs signed with HS256. Signed, not encrypted: never put secrets in
  custom claims.

${sections}

## Project

- [Source](${site.links.github})
- [PyPI](${site.links.pypi})
- [Issues](${site.links.issues})

Authored by ${site.author.name}, founder of ${site.company.name}.
`;

  return new Response(body, {
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "public, max-age=3600",
    },
  });
}
