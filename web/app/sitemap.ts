import type { MetadataRoute } from "next";
import { docsFlat } from "@/lib/nav";
import { site } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  return [
    {
      url: site.url,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
    },
    ...docsFlat.map((doc) => ({
      url: `${site.url}${doc.href}`,
      lastModified: now,
      changeFrequency: "monthly" as const,
      // The overview and the two entry-point pages matter most for search.
      priority: ["/docs", "/docs/quick-start", "/docs/easy-mode"].includes(doc.href)
        ? 0.9
        : 0.7,
    })),
  ];
}
