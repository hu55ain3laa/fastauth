# FastAuth documentation site

The marketing page and documentation for [FastAuth](https://github.com/hu55ain3laa/fastauth),
built with Next.js 16 (App Router), Tailwind v4, and MDX.

Built by Hussein Ghadhban, founder of [Pythowner](https://pythowner.com).

## Running it

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # production build
pnpm lint
```

## Deploying to Vercel

Import the repository, then set **Root Directory** to `web`. Framework preset
and build command are detected automatically.

Set one environment variable so canonical URLs, the sitemap, robots.txt, and the
Open Graph image point at the real domain:

```
NEXT_PUBLIC_SITE_URL=https://your-domain
```

Without it the site falls back to the placeholder in `lib/site.ts`.

## How it is put together

```
app/
  page.tsx              landing page
  docs/
    layout.tsx          sidebar + prev/next shell
    <slug>/page.mdx     one file per documentation page
  sitemap.ts robots.ts opengraph-image.tsx icon.svg
components/
  landing/              hero, features, quick look
  ...                   code-block, callout, steps, endpoints, jwt-decoder
lib/
  site.ts               version, links, authorship — the single source of truth
  nav.ts                the docs outline (sidebar, footer, pager, sitemap)
  highlight.ts          Shiki highlighter + the FastAuth syntax theme
mdx-components.tsx      element mapping + components available in every .mdx
```

### Adding a documentation page

1. Create `app/docs/<slug>/page.mdx` with an exported `metadata` object.
2. Add an entry to the right group in `lib/nav.ts`.

The sidebar, the footer columns, the prev/next pager, and the sitemap all read
from that one array, so there is nothing else to update.

### Writing MDX

Code fences carry the panel label after a colon:

````md
```python:main.py
auth.setup(app)
```
````

These components are in scope in every `.mdx` file without an import:
`Callout`, `Checkpoint`, `CodeBlock`, `DocIndex`, `Endpoint`, `EndpointList`,
`Eyebrow`, `Fix`, `Fixes`, `Lede`, `Step`, `Steps`.

Use `<Lede>` and `<Eyebrow>` rather than a raw `<p>` with a class. MDX wraps
multi-line JSX children in their own paragraph, and a `<p>` inside a `<p>` is
invalid HTML that breaks hydration.

## Design system

Tokens live at the top of `app/globals.css`: dark by default, light applied via
`html.light`, with the toggle persisting to `localStorage` and an inline script
in the layout applying it before first paint. Code panels stay dark in both
themes, the way an editor does. Accent is FastAuth's brand teal, brightened on
dark surfaces for contrast.
