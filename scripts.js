// ---------------------------------------------------------------------------
// Theme toggle — persists choice, follows system preference until overridden
// ---------------------------------------------------------------------------
const themeToggle = document.getElementById("theme-toggle");

function applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.dataset.theme = "dark";
  } else {
    delete document.documentElement.dataset.theme;
  }
  document.documentElement.style.colorScheme = theme;
}

themeToggle.addEventListener("click", () => {
  const next =
    document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("theme", next);
});

window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", (e) => {
    if (!localStorage.getItem("theme")) {
      applyTheme(e.matches ? "dark" : "light");
    }
  });

// ---------------------------------------------------------------------------
// Copy buttons — .js-copy uses data-copy; bare .copy-btn copies its panel code
// ---------------------------------------------------------------------------
function flash(button) {
  const icon = button.querySelector(".ph");
  if (!icon) return;
  icon.classList.replace("ph-copy", "ph-check");
  setTimeout(() => {
    icon.classList.replace("ph-check", "ph-copy");
  }, 1400);
}

document.querySelectorAll(".copy-btn, .js-copy").forEach((button) => {
  button.addEventListener("click", () => {
    let text = button.dataset.copy;
    if (!text) {
      const panel = button.closest(".panel");
      const code = panel && panel.querySelector("code");
      text = code ? code.textContent : "";
    }
    navigator.clipboard.writeText(text).then(() => flash(button));
  });
});

// ---------------------------------------------------------------------------
// Sidebar scrollspy — highlight the section currently in view
// ---------------------------------------------------------------------------
const tocLinks = Array.from(document.querySelectorAll(".toc a"));
const sections = tocLinks
  .map((link) => document.querySelector(link.getAttribute("href")))
  .filter(Boolean);

function setActive(id) {
  tocLinks.forEach((link) =>
    link.classList.toggle("active", link.getAttribute("href") === "#" + id)
  );
}

if ("IntersectionObserver" in window && sections.length) {
  const visible = new Set();
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visible.add(entry.target.id);
        else visible.delete(entry.target.id);
      });
      // Highlight the visible section closest to the top of the page
      const first = sections.find((section) => visible.has(section.id));
      if (first) setActive(first.id);
    },
    { rootMargin: "-20% 0px -60% 0px" }
  );
  sections.forEach((section) => observer.observe(section));
}

// Collapse the mobile ToC after choosing a destination
const mobileToc = document.querySelector(".toc-mobile");
if (mobileToc) {
  mobileToc.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => mobileToc.removeAttribute("open"));
  });
}

// ---------------------------------------------------------------------------
// Token decoder — hovering a segment highlights its decoded claims (and back)
// ---------------------------------------------------------------------------
const decoder = document.getElementById("decoder");
if (decoder) {
  decoder.querySelectorAll("[data-seg]").forEach((el) => {
    el.addEventListener("mouseenter", () => {
      decoder.classList.add("hl-" + el.dataset.seg);
    });
    el.addEventListener("mouseleave", () => {
      decoder.classList.remove("hl-" + el.dataset.seg);
    });
  });
}
