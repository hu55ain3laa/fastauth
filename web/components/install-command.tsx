import { CopyButton } from "./copy-button";
import { site } from "@/lib/site";

export function InstallCommand({
  command = site.install,
  className = "inline-flex",
}: {
  command?: string;
  className?: string;
}) {
  return (
    <span
      className={`${className} min-w-0 items-center gap-2.5 rounded-xl border border-line bg-surface-2/70 py-2.5 pl-4 pr-2.5 font-mono text-[0.8125rem] text-foreground backdrop-blur`}
    >
      <span className="select-none text-accent" aria-hidden>
        $
      </span>
      <span className="min-w-0 flex-1 truncate">{command}</span>
      <CopyButton
        text={command}
        label="Copy install command"
        className="inline-flex items-center rounded-md border border-transparent p-1.5 text-muted-2 transition-colors hover:bg-surface-2 hover:text-accent"
      />
    </span>
  );
}
