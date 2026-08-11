"use client";

import { useState } from "react";
import { Check, Copy } from "@phosphor-icons/react/dist/ssr";

export function CopyButton({
  text,
  label = "Copy code",
  className = "code-copy",
}: {
  text: string;
  label?: string;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard access can be denied; leaving the icon unchanged is the
      // honest signal that nothing was copied.
    }
  }

  return (
    <button type="button" onClick={copy} aria-label={label} className={className}>
      {copied ? <Check size={14} weight="bold" /> : <Copy size={14} />}
      <span className="sr-only">{copied ? "Copied" : label}</span>
    </button>
  );
}
