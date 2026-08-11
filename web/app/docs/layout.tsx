import { DocsSidebar } from "@/components/docs-sidebar";
import { DocPager } from "@/components/doc-pager";
import { ReadingModeToggle } from "@/components/reading-mode-toggle";

export default function DocsLayout({ children }: LayoutProps<"/docs">) {
  return (
    <div className="docs-shell mx-auto flex max-w-7xl gap-12 px-4 sm:px-6 lg:px-8">
      <aside className="docs-sidebar hidden w-56 shrink-0 lg:block">
        <div className="sticky top-[calc(var(--topbar-h)+2rem)] max-h-[calc(100vh-var(--topbar-h)-4rem)] overflow-y-auto overscroll-y-contain py-12 scrollbar-none">
          <DocsSidebar />
        </div>
      </aside>

      <div className="docs-body min-w-0 flex-1 py-12 lg:py-14">
        <div className="docs-measure mb-8 flex justify-end">
          <ReadingModeToggle />
        </div>
        <article className="prose-fa docs-measure">{children}</article>
        <div className="docs-measure">
          <DocPager />
        </div>
      </div>
    </div>
  );
}
