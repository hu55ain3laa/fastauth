/**
 * The documentation outline. This single list drives the sidebar, the mobile
 * menu, the prev/next footer links, and the sitemap, so adding a page means
 * editing one array.
 */
export type DocLink = {
  href: string;
  label: string;
  summary: string;
};

export type DocGroup = {
  label: string;
  items: DocLink[];
};

export const docsNav: DocGroup[] = [
  {
    label: "Start",
    items: [
      {
        href: "/docs",
        label: "Overview",
        summary: "What FastAuth does and how the pieces fit together.",
      },
      {
        href: "/docs/concepts",
        label: "How auth works",
        summary:
          "Hashing, tokens, cookies, and roles explained from scratch. Start here if the vocabulary is new.",
      },
      {
        href: "/docs/installation",
        label: "Installation",
        summary: "Add FastAuth to a project, with or without uv.",
      },
      {
        href: "/docs/quick-start",
        label: "Quick start",
        summary: "A complete app with login, refresh, roles, and protected routes.",
      },
      {
        href: "/docs/easy-mode",
        label: "Easy mode",
        summary: "One file, five minutes, every step checked. For first-timers.",
      },
    ],
  },
  {
    label: "Guide",
    items: [
      {
        href: "/docs/authentication",
        label: "Authentication",
        summary: "Tokens, protected routes, and cookie-based sessions.",
      },
      {
        href: "/docs/account-flows",
        label: "Account flows",
        summary: "Password reset, password change, and email verification.",
      },
      {
        href: "/docs/database",
        label: "Database setup",
        summary: "Create tables, standard roles, and a superadmin.",
      },
      {
        href: "/docs/roles",
        label: "Roles",
        summary: "Role-based authorization and the role management API.",
      },
      {
        href: "/docs/customization",
        label: "Customization",
        summary: "From zero config to composing the primitives yourself.",
      },
    ],
  },
  {
    label: "Reference",
    items: [
      {
        href: "/docs/production",
        label: "Production",
        summary: "The safety rails FastAuth enforces, and a deploy checklist.",
      },
      {
        href: "/docs/endpoints",
        label: "Endpoints",
        summary: "Every route auth.setup(app) mounts.",
      },
      {
        href: "/docs/errors",
        label: "Error handling",
        summary: "One JSON shape and a machine-readable code for every failure.",
      },
      {
        href: "/docs/troubleshooting",
        label: "Troubleshooting",
        summary: "Find your error message and the thing that fixes it.",
      },
      {
        href: "/docs/advanced",
        label: "Advanced usage",
        summary: "Custom user models and custom authentication logic.",
      },
      {
        href: "/docs/security",
        label: "Security",
        summary: "Practices worth following before you ship.",
      },
      {
        href: "/docs/versioning",
        label: "Versioning",
        summary:
          "What each number in a release means, and how deprecations are announced and removed.",
      },
      {
        href: "/docs/project-structure",
        label: "Project structure",
        summary: "How the package is laid out.",
      },
    ],
  },
];

/** Flat, in-reading-order list. Used for prev/next and the sitemap. */
export const docsFlat: DocLink[] = docsNav.flatMap((group) => group.items);

export function docNeighbours(pathname: string) {
  const index = docsFlat.findIndex((item) => item.href === pathname);
  if (index === -1) return { prev: undefined, next: undefined };
  return {
    prev: index > 0 ? docsFlat[index - 1] : undefined,
    next: index < docsFlat.length - 1 ? docsFlat[index + 1] : undefined,
  };
}
