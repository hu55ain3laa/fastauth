/**
 * One place for every fact the site repeats: canonical URL, version, links,
 * and authorship. Change the domain here (or via NEXT_PUBLIC_SITE_URL) and
 * metadata, sitemap, robots, and JSON-LD all follow.
 */
export const site = {
  name: "FastAuth",
  tagline: "Authentication for FastAPI, wired in one call",
  description:
    "FastAuth adds JWT access and refresh tokens, role-based access control, and ready-made login routes to any FastAPI + SQLModel app.",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "https://fastauth.pythowner.com",
  version: "0.7.0",
  package: "fastauth_iq",
  install: 'uv add fastauth_iq "fastapi[standard]"',
  links: {
    github: "https://github.com/hu55ain3laa/fastauth",
    issues: "https://github.com/hu55ain3laa/fastauth/issues",
    pypi: "https://pypi.org/project/fastauth-iq/",
    ci: "https://github.com/hu55ain3laa/fastauth/actions/workflows/ci.yml",
  },
  author: {
    name: "Hussein Ghadhban",
    url: "https://www.hu55ain3laa.site",
    role: "Founder of Pythowner",
  },
  company: {
    name: "Pythowner",
    legalName: "Pythowner LLC",
    url: "https://pythowner.com",
  },
} as const;
