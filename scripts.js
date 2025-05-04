// Check for saved theme preference or use the system preference
const themeToggleBtn = document.getElementById("theme-toggle");

// Function to set theme
function setTheme(theme) {
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");

  if (theme === "dark") {
    document.documentElement.classList.add("dark");
    document.documentElement.style.colorScheme = "dark";
    localStorage.setItem("theme", "dark");
    // Update icons
    sunIcon.classList.remove("hidden");
    sunIcon.classList.add("block");
    moonIcon.classList.remove("block");
    moonIcon.classList.add("hidden");
  } else {
    document.documentElement.classList.remove("dark");
    document.documentElement.style.colorScheme = "light";
    localStorage.setItem("theme", "light");
    // Update icons
    moonIcon.classList.remove("hidden");
    moonIcon.classList.add("block");
    sunIcon.classList.remove("block");
    sunIcon.classList.add("hidden");
  }
}

// Check for saved theme preference
const savedTheme = localStorage.getItem("theme");

// If user has a saved preference, use it
if (savedTheme) {
  setTheme(savedTheme);
}
// Otherwise, use system preference
else if (
  window.matchMedia &&
  window.matchMedia("(prefers-color-scheme: dark)").matches
) {
  setTheme("dark");
}

// Add click event to toggle button
themeToggleBtn.addEventListener("click", () => {
  if (document.documentElement.classList.contains("dark")) {
    setTheme("light");
  } else {
    setTheme("dark");
  }
});

// Watch for system preference changes
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", (e) => {
    if (!localStorage.getItem("theme")) {
      // Only react if user hasn't manually set a preference
      setTheme(e.matches ? "dark" : "light");
    }
  });


// Mobile Navigation Menu functionality
document.addEventListener('DOMContentLoaded', function() {
  const mobileMenuButton = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  
  if (mobileMenuButton && mobileMenu) {
    // Toggle mobile menu when button is clicked
    mobileMenuButton.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });
    
    // Hide mobile menu when clicking on menu items that aren't in collapsible sections
    const mobileMenuItems = mobileMenu.querySelectorAll('a:not(.mobile-section-content a)');
    mobileMenuItems.forEach(item => {
      item.addEventListener('click', function() {
        mobileMenu.classList.add('hidden');
      });
    });
    
    // Handle visibility on resize
    window.addEventListener('resize', function() {
      if (window.innerWidth >= 768) {
        mobileMenu.classList.add('hidden');
      }
    });
  }
});

// Function to toggle collapsible sections in mobile menu
function toggleMobileSection(button) {
  // Toggle the hidden class on the next sibling element (content)
  const content = button.nextElementSibling;
  content.classList.toggle('hidden');
  
  // Rotate the arrow icon
  const icon = button.querySelector('svg');
  if (content.classList.contains('hidden')) {
    icon.style.transform = 'rotate(0deg)';
  } else {
    icon.style.transform = 'rotate(180deg)';
  }
}
