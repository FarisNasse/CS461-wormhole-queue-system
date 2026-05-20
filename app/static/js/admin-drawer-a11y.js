document.addEventListener("DOMContentLoaded", () => {
  const drawer = document.getElementById("admin-drawer");

  if (!drawer) {
    return;
  }

  const syncDrawerAccessibility = () => {
    const isClosed = drawer.classList.contains("translate-x-full");

    drawer.toggleAttribute("inert", isClosed);
    drawer.setAttribute("aria-hidden", isClosed ? "true" : "false");
  };

  syncDrawerAccessibility();

  const observer = new MutationObserver(syncDrawerAccessibility);
  observer.observe(drawer, {
    attributes: true,
    attributeFilter: ["class"],
  });
});
