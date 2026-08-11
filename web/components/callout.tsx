import type { ReactNode } from "react";
import {
  GraduationCap,
  Info,
  Lightbulb,
  Warning,
} from "@phosphor-icons/react/dist/ssr";

const VARIANTS = {
  note: { Icon: Info, tone: "text-accent", ring: "border-accent-line" },
  tip: { Icon: Lightbulb, tone: "text-accent", ring: "border-accent-line" },
  learn: { Icon: GraduationCap, tone: "text-violet", ring: "border-line" },
  warning: { Icon: Warning, tone: "text-amber", ring: "border-line" },
} as const;

export function Callout({
  variant = "note",
  children,
}: {
  variant?: keyof typeof VARIANTS;
  children: ReactNode;
}) {
  const { Icon, tone, ring } = VARIANTS[variant] ?? VARIANTS.note;

  return (
    <div className={`my-6 flex gap-3.5 rounded-xl border ${ring} bg-surface-2/60 p-4`}>
      <Icon size={19} className={`mt-0.5 shrink-0 ${tone}`} weight="fill" />
      <div className="min-w-0 text-[0.9375rem] leading-relaxed text-muted [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
        {children}
      </div>
    </div>
  );
}
