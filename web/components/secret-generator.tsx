"use client";

import { useState } from "react";
import { ArrowsClockwise, Check, Copy } from "@phosphor-icons/react/dist/ssr";

/**
 * Generates a signing key right in the page, so nobody has to go and find
 * openssl. Uses the browser's CSPRNG — the same source a server would use —
 * and the value never leaves the page.
 */
export function SecretGenerator() {
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  function generate() {
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    setSecret(
      Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
    );
    setCopied(false);
  }

  async function copy() {
    if (!secret) return;
    try {
      await navigator.clipboard.writeText(secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard denied; the value stays on screen to select manually.
    }
  }

  return (
    <div className="my-6 rounded-xl border border-accent-line bg-accent-soft/40 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-accent">
          Generate a secret key
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={generate}
            className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-foreground transition-colors hover:border-line-strong"
          >
            <ArrowsClockwise size={13} />
            {secret ? "Again" : "Generate"}
          </button>
          {secret && (
            <button
              type="button"
              onClick={copy}
              aria-label="Copy secret key"
              className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-surface px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider text-foreground transition-colors hover:border-line-strong"
            >
              {copied ? <Check size={13} weight="bold" /> : <Copy size={13} />}
              {copied ? "Copied" : "Copy"}
            </button>
          )}
        </div>
      </div>

      <p className="mt-3 break-all rounded-lg border border-line bg-[var(--editor)] px-3 py-2.5 font-mono text-[12.5px] text-[#6fd4c8]">
        {secret ?? (
          <span className="text-[#6d837e]">
            32 random bytes, hex encoded — press Generate
          </span>
        )}
      </p>

      <p className="mt-2.5 text-xs leading-relaxed text-muted">
        Generated in your browser and never sent anywhere. Put it in{" "}
        <code className="font-mono text-accent">SECRET_KEY</code> in your
        environment, not in your source code.
      </p>
    </div>
  );
}
