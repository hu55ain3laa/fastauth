import type { Metadata, Viewport } from "next";
import { Archivo, Spline_Sans_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { SoftwareJsonLd } from "@/components/seo/software-jsonld";
import { site } from "@/lib/site";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  display: "swap",
});

const splineMono = Spline_Sans_Mono({
  variable: "--font-spline-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#08100f" },
    { media: "(prefers-color-scheme: light)", color: "#f3f6f5" },
  ],
};

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: `${site.name} · ${site.tagline}`,
    template: `%s · ${site.name}`,
  },
  description: site.description,
  applicationName: site.name,
  authors: [{ name: site.author.name, url: site.author.url }],
  creator: site.author.name,
  publisher: site.company.legalName,
  category: "Developer Tools",
  keywords: [
    "FastAPI authentication",
    "FastAPI JWT",
    "FastAPI OAuth2",
    "SQLModel auth",
    "Python authentication library",
    "FastAPI role based access control",
    "FastAPI refresh token",
    "FastAPI login routes",
    "fastauth_iq",
    "FastAuth",
  ],
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: site.name,
    title: `${site.name} · ${site.tagline}`,
    description: site.description,
    url: site.url,
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: `${site.name} · ${site.tagline}`,
    description: site.description,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

/**
 * Applied before first paint so a light-theme reader never sees a dark flash,
 * and reading mode never flashes the sidebar in and out. Dark is the default,
 * matching the server-rendered `class="dark"`.
 */
const themeScript = `(function(){try{var d=document.documentElement;if(localStorage.getItem("fastauth-theme")==="light"){d.classList.remove("dark");d.classList.add("light")}if(localStorage.getItem("fastauth-reading")==="on"){d.classList.add("reading")}}catch(e){}})();`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`dark h-full ${archivo.variable} ${splineMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      {/* Browser extensions commonly stamp attributes onto <body> before React
          hydrates. suppressHydrationWarning only covers one level, so it is
          needed here as well as on <html>. */}
      <body
        suppressHydrationWarning
        className="min-h-full flex flex-col bg-background text-foreground antialiased"
      >
        <SoftwareJsonLd />
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:m-3 focus:rounded-lg focus:bg-accent focus:px-4 focus:py-2 focus:text-accent-ink"
        >
          Skip to content
        </a>
        <Navbar />
        <main id="main" className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
