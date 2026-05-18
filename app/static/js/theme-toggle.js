document.addEventListener("DOMContentLoaded", () => {
  const themeToggleButton = document.getElementById("theme-toggle");
  const darkIcon = document.getElementById("theme-toggle-dark-icon");
  const lightIcon = document.getElementById("theme-toggle-light-icon");

  if (!themeToggleButton || !darkIcon || !lightIcon) {
    return;
  }

  function updateThemeToggle() {
    const isDark = document.documentElement.classList.contains("dark");

    darkIcon.classList.toggle("hidden", isDark);
    lightIcon.classList.toggle("hidden", !isDark);
    themeToggleButton.setAttribute("aria-pressed", isDark ? "true" : "false");
    themeToggleButton.setAttribute(
      "aria-label",
      isDark ? "Switch to light mode" : "Switch to dark mode",
    );
  }

  updateThemeToggle();

  themeToggleButton.addEventListener("click", () => {
    const isDark = document.documentElement.classList.toggle("dark");

    localStorage.setItem("color-theme", isDark ? "dark" : "light");
    updateThemeToggle();
  });
});
