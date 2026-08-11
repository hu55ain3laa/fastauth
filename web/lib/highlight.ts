import { createHighlighter, type Highlighter, type ThemeRegistrationRaw } from "shiki";

/**
 * FastAuth's syntax palette, expressed as a TextMate theme so Shiki produces
 * the same colours the hand-written site used: rose keywords, teal strings,
 * violet functions, amber numbers, on the near-black editor surface.
 */
const fastauthTheme: ThemeRegistrationRaw = {
  name: "fastauth",
  type: "dark",
  colors: {
    "editor.background": "#0a1211",
    "editor.foreground": "#d9e6e3",
  },
  settings: [
    { settings: { background: "#0a1211", foreground: "#d9e6e3" } },
    {
      scope: ["comment", "punctuation.definition.comment"],
      settings: { foreground: "#6d837e", fontStyle: "italic" },
    },
    {
      scope: [
        "keyword",
        "storage",
        "storage.type",
        "keyword.control",
        "keyword.operator.logical",
        "keyword.operator.new",
        "entity.name.tag",
      ],
      settings: { foreground: "#ef8ba0" },
    },
    {
      scope: ["string", "string.quoted", "punctuation.definition.string", "meta.string"],
      settings: { foreground: "#6fd4c8" },
    },
    {
      scope: [
        "entity.name.function",
        "support.function",
        "meta.function-call.generic",
        "variable.function",
      ],
      settings: { foreground: "#b3a9f2" },
    },
    {
      scope: ["constant.numeric", "constant.language", "constant.character", "constant.other"],
      settings: { foreground: "#e4b568" },
    },
    {
      scope: [
        "entity.name.class",
        "entity.name.type",
        "support.class",
        "support.type",
        "entity.other.inherited-class",
      ],
      settings: { foreground: "#8fd8cd" },
    },
    {
      scope: ["entity.name.function.decorator", "meta.decorator", "punctuation.decorator"],
      settings: { foreground: "#e4b568" },
    },
    {
      scope: ["support.type.property-name", "meta.object-literal.key"],
      settings: { foreground: "#b3a9f2" },
    },
    {
      scope: ["punctuation", "meta.brace", "keyword.operator"],
      settings: { foreground: "#8fa5a0" },
    },
    {
      scope: ["variable.parameter", "variable.other"],
      settings: { foreground: "#d9e6e3" },
    },
  ],
};

const LANGS = ["python", "bash", "json", "text", "toml", "sql"] as const;

// One highlighter for the whole build. Creating a highlighter per code block
// loads the WASM grammar engine each time and makes builds crawl.
let highlighterPromise: Promise<Highlighter> | undefined;

function getHighlighter() {
  highlighterPromise ??= createHighlighter({
    themes: [fastauthTheme],
    langs: [...LANGS],
  });
  return highlighterPromise;
}

export async function highlight(code: string, lang: string): Promise<string> {
  const highlighter = await getHighlighter();
  const loaded = highlighter.getLoadedLanguages();
  const language = loaded.includes(lang) ? lang : "text";
  return highlighter.codeToHtml(code, { lang: language, theme: "fastauth" });
}
