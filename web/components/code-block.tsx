import { highlight } from "@/lib/highlight";
import { CopyButton } from "./copy-button";

const LABELS: Record<string, string> = {
  python: "python",
  bash: "shell",
  json: "json",
  toml: "toml",
  sql: "sql",
  text: "text",
};

export async function CodeBlock({
  code,
  lang = "text",
  file,
  className = "",
  compact = false,
  wrap = false,
}: {
  code: string;
  lang?: string;
  /** Shown in the panel bar, e.g. "main.py". Falls back to the language. */
  file?: string;
  className?: string;
  /** Tighter type and padding, for code sitting inside a card. */
  compact?: boolean;
  /** Wrap long lines instead of scrolling them. Use in narrow containers. */
  wrap?: boolean;
}) {
  const source = code.replace(/\n$/, "");
  const html = await highlight(source, lang);

  return (
    <div
      className={`code-panel min-w-0 ${compact ? "code-panel--compact" : ""} ${
        wrap ? "code-panel--wrap" : ""
      } ${className}`}
    >
      <div className="code-panel__bar">
        <span className="truncate">{file ?? LABELS[lang] ?? lang}</span>
        <CopyButton text={source} />
      </div>
      <div
        className="min-w-0 scrollbar-none"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
