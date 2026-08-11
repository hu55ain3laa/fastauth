import { site } from "@/lib/site";

/**
 * SoftwareSourceCode + Organization structured data. Search engines use this
 * to attribute the library to its author and publisher, which is why the
 * Pythowner founder credit lives here as well as in the footer.
 */
export function SoftwareJsonLd() {
  const author = {
    "@type": "Person",
    name: site.author.name,
    url: site.author.url,
    jobTitle: "Founder",
    worksFor: {
      "@type": "Organization",
      name: site.company.legalName,
      url: site.company.url,
    },
  };

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareSourceCode",
        name: site.name,
        description: site.description,
        url: site.url,
        codeRepository: site.links.github,
        programmingLanguage: "Python",
        runtimePlatform: "Python 3.10+",
        license: "https://opensource.org/licenses/MIT",
        version: site.version,
        author,
        maintainer: author,
        publisher: {
          "@type": "Organization",
          name: site.company.legalName,
          url: site.company.url,
        },
      },
      {
        "@type": "SoftwareApplication",
        name: site.name,
        applicationCategory: "DeveloperApplication",
        operatingSystem: "Any",
        softwareVersion: site.version,
        description: site.description,
        url: site.url,
        downloadUrl: site.links.pypi,
        author,
        offers: {
          "@type": "Offer",
          price: "0",
          priceCurrency: "USD",
        },
      },
      {
        "@type": "WebSite",
        name: site.name,
        url: site.url,
        inLanguage: "en",
        author,
      },
    ],
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}
