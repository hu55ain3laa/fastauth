/**
 * Builds the docs search index.
 *
 * Reads every app/docs/(slug)/page.mdx, strips the MDX machinery, and splits
 * each page into one record per heading so a hit can link straight to the
 * relevant section rather than the top of a long page.
 *
 * Runs before `dev` and `build`; the output is generated, not committed.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { globSync } from "node:fs";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

/** GitHub-style slug, matching what rehype-slug generates for headings. */
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

/** Reduce MDX to readable prose: no imports, JSX, code fences, or markup. */
function toProse(mdx) {
  return mdx
    .replace(/^export const metadata[\s\S]*?^};/m, "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\{["'`][\s\S]*?["'`]\}/g, " ") // JSX string expressions like {" "}
    .replace(/<[^>]+>/g, " ")
    .replace(/^#{1,6}\s+.*$/gm, " ") // headings are captured separately
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/[*_`|]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function titleOf(mdx, fallback) {
  const m = mdx.match(/^#\s+(.+)$/m);
  return m ? m[1].trim() : fallback;
}

const files = globSync("app/docs/**/page.mdx", { cwd: root });
const records = [];

for (const file of files) {
  const mdx = readFileSync(join(root, file), "utf8");
  const dir = dirname(file);
  const slug = relative("app", dir).replace(/\\/g, "/");
  const href = "/" + slug.replace(/\/?page$/, "");
  const pageTitle = titleOf(mdx, slug);

  // Split on h2/h3 so each section becomes its own searchable record.
  const parts = mdx.split(/^(##{1,2})\s+(.+)$/m);
  const intro = toProse(parts[0]);
  if (intro) {
    records.push({ href, page: pageTitle, heading: null, text: intro.slice(0, 600) });
  }
  for (let i = 1; i < parts.length; i += 3) {
    const heading = parts[i + 1]?.trim();
    const body = toProse(parts[i + 2] ?? "");
    if (!heading) continue;
    records.push({
      href: `${href}#${slugify(heading)}`,
      page: pageTitle,
      heading,
      text: body.slice(0, 600),
    });
  }
}

mkdirSync(join(root, "public"), { recursive: true });
writeFileSync(
  join(root, "public/search-index.json"),
  JSON.stringify(records),
  "utf8"
);

console.log(
  `search index: ${records.length} sections from ${files.length} pages`
);
