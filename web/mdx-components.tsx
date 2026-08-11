import { isValidElement, type ComponentPropsWithoutRef, type ReactNode } from "react";
import Link from "next/link";
import type { MDXComponents } from "mdx/types";
import { CodeBlock } from "@/components/code-block";
import { Callout } from "@/components/callout";
import { Endpoint, EndpointList } from "@/components/endpoints";
import { Step, Steps } from "@/components/steps";
import { DocIndex } from "@/components/doc-index";
import { Checkpoint, Fix, Fixes } from "@/components/checkpoint";
import { Eyebrow, Lede } from "@/components/prose";
import { JwtDecoder } from "@/components/jwt-decoder";
import { ResetFlowDiagram, TokenFlowDiagram } from "@/components/diagrams";
import { SecretGenerator } from "@/components/secret-generator";
import { Tabs } from "@/components/tabs";

type CodeProps = { className?: string; children?: ReactNode };

/**
 * Fences carry the filename after a colon, e.g. ```python:main.py — that keeps
 * the panel label in the markdown without needing a custom rehype plugin,
 * which Turbopack cannot load from a local file anyway.
 */
function parseFence(className: string | undefined) {
  const raw = (className ?? "").replace(/^language-/, "");
  const [lang, file] = raw.split(":");
  return { lang: lang || "text", file: file || undefined };
}

/** A heading that reveals a `#` permalink on hover, like the old site's. */
function heading(level: 2 | 3 | 4) {
  const Tag = `h${level}` as const;
  const sizes = {
    2: "mt-14 mb-4 scroll-mt-24 text-[1.6rem] font-bold tracking-tight",
    3: "mt-10 mb-3 scroll-mt-24 text-xl font-semibold tracking-tight",
    4: "mt-8 mb-2 scroll-mt-24 text-base font-semibold tracking-tight",
  } as const;

  return function Heading({ id, children, ...rest }: ComponentPropsWithoutRef<"h2">) {
    return (
      <Tag id={id} className={`group text-foreground ${sizes[level]}`} {...rest}>
        {children}
        {id && (
          <a
            href={`#${id}`}
            aria-label="Link to this section"
            className="ml-2 font-mono text-[0.7em] text-accent opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
          >
            #
          </a>
        )}
      </Tag>
    );
  };
}

const components: MDXComponents = {
  // Available in every .mdx file without an import.
  Callout,
  Checkpoint,
  CodeBlock,
  DocIndex,
  Endpoint,
  EndpointList,
  Eyebrow,
  Fix,
  Fixes,
  JwtDecoder,
  Lede,
  ResetFlowDiagram,
  SecretGenerator,
  Step,
  Steps,
  Tabs,
  TokenFlowDiagram,

  h1: ({ children, ...rest }: ComponentPropsWithoutRef<"h1">) => (
    <h1
      className="mb-4 text-[clamp(2rem,4.2vw,2.9rem)] font-bold leading-[1.1] tracking-tight text-foreground"
      {...rest}
    >
      {children}
    </h1>
  ),
  h2: heading(2),
  h3: heading(3),
  h4: heading(4),

  pre: ({ children }: ComponentPropsWithoutRef<"pre">) => {
    if (!isValidElement<CodeProps>(children)) return <pre>{children}</pre>;
    const { lang, file } = parseFence(children.props.className);
    const code =
      typeof children.props.children === "string" ? children.props.children : "";
    return <CodeBlock code={code} lang={lang} file={file} className="my-6" />;
  },

  a: ({ href = "", children, ...rest }: ComponentPropsWithoutRef<"a">) => {
    const internal = href.startsWith("/") || href.startsWith("#");
    if (internal) {
      return (
        <Link href={href} className="text-accent underline underline-offset-2 hover:opacity-80">
          {children}
        </Link>
      );
    }
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-accent underline underline-offset-2 hover:opacity-80"
        {...rest}
      >
        {children}
      </a>
    );
  },

  // `> quoted text` in markdown becomes a note callout.
  blockquote: ({ children }: ComponentPropsWithoutRef<"blockquote">) => (
    <Callout variant="note">{children}</Callout>
  ),

  table: ({ children, ...rest }: ComponentPropsWithoutRef<"table">) => (
    <div className="my-6 overflow-x-auto rounded-xl border border-line">
      <table className="w-full border-collapse text-sm" {...rest}>
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...rest }: ComponentPropsWithoutRef<"th">) => (
    <th
      className="border-b border-line bg-surface-2/60 px-4 py-2.5 text-left font-mono text-[10.5px] uppercase tracking-[0.14em] text-muted-2"
      {...rest}
    >
      {children}
    </th>
  ),
  td: ({ children, ...rest }: ComponentPropsWithoutRef<"td">) => (
    <td className="border-b border-line px-4 py-2.5 align-top text-muted last:[&:not(:first-child)]:text-muted" {...rest}>
      {children}
    </td>
  ),
};

export function useMDXComponents(): MDXComponents {
  return components;
}
