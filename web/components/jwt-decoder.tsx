"use client";

import { useState } from "react";
import { SealCheck } from "@phosphor-icons/react/dist/ssr";

type Segment = "header" | "payload" | "signature";

const TOKEN: Record<Segment, string> = {
  header: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
  payload:
    "eyJzdWIiOiJodXNzZWluIiwidG9rZW5fdHlwZSI6ImFjY2VzcyIsImV4cCI6MTc1NTA0MzIwMH0",
  signature: "yBQbNKYIhBNfoarNn5A_5z8EaLbyZbnPMLOyvBCKhO4",
};

const SEG_COLOR: Record<Segment, string> = {
  header: "text-[#ef8ba0]",
  payload: "text-[#b3a9f2]",
  signature: "text-[#6fd4c8]",
};

const CLAIMS: { seg: Segment; k: string; v: string }[] = [
  { seg: "header", k: "alg · typ", v: '"HS256" · "JWT"' },
  { seg: "payload", k: "sub", v: '"hussein"' },
  { seg: "payload", k: "token_type", v: '"access"' },
  { seg: "payload", k: "exp", v: "1755043200" },
];

/**
 * A real access token, decoded. Hovering a segment of the encoded token lights
 * up the claims it carries, and vice versa, so the three-part structure of a
 * JWT is legible at a glance.
 */
export function JwtDecoder() {
  const [active, setActive] = useState<Segment | null>(null);

  const hoverProps = (seg: Segment) => ({
    onMouseEnter: () => setActive(seg),
    onMouseLeave: () => setActive(null),
    onFocus: () => setActive(seg),
    onBlur: () => setActive(null),
  });

  const lit = (seg: Segment) =>
    active === seg ? "bg-white/[0.09]" : "bg-transparent";

  return (
    <div
      className="rounded-2xl border border-white/10 bg-[var(--editor)] p-5 shadow-[0_24px_60px_-30px_rgba(0,0,0,0.9)] sm:p-6"
      role="img"
      aria-label="A JSON Web Token split into its header, payload, and signature segments, decoded into its claims, with the signature verified"
    >
      <div className="mb-4 flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.16em] text-[#6d837e]">
        <span>access_token</span>
        <span>jwt · hs256</span>
      </div>

      <div
        className="mb-5 break-all font-mono text-[0.78rem] leading-[1.85]"
        aria-hidden
      >
        {(Object.keys(TOKEN) as Segment[]).map((seg, i) => (
          <span key={seg}>
            {i > 0 && <span className="text-[#6d837e]">.</span>}
            <span
              {...hoverProps(seg)}
              tabIndex={0}
              className={`rounded-[4px] px-[0.1em] py-[0.05em] transition-colors ${SEG_COLOR[seg]} ${lit(seg)}`}
            >
              {TOKEN[seg]}
            </span>
          </span>
        ))}
      </div>

      <div className="space-y-0.5 border-t border-white/[0.07] pt-4 font-mono text-[0.78rem]" aria-hidden>
        {CLAIMS.map((claim) => (
          <div
            key={claim.k}
            {...hoverProps(claim.seg)}
            className={`flex items-center justify-between gap-4 rounded-[5px] px-1.5 py-1 transition-colors ${
              active === claim.seg ? "bg-white/[0.06]" : ""
            }`}
          >
            <span className="text-[#6d837e]">{claim.k}</span>
            <span className={SEG_COLOR[claim.seg]}>{claim.v}</span>
          </div>
        ))}
      </div>

      <div
        {...hoverProps("signature")}
        className={`mt-3 flex items-center gap-2 rounded-[5px] px-1.5 py-1.5 font-mono text-[0.72rem] text-[#6fd4c8] transition-colors ${
          active === "signature" ? "bg-white/[0.06]" : ""
        }`}
        aria-hidden
      >
        <SealCheck size={15} weight="fill" />
        signature verified with your secret_key
      </div>
    </div>
  );
}
