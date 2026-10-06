/**
 * Progressive disclosure menu panel handler.
 * Closes on Escape and clicks outside, restoring focus to summary element.
 */
export function initMenuPanel() {
  const details = document.querySelector(".shop-menu-details");
  if (!details) return;

  const summary = details.querySelector(".shop-menu-summary");

  document.addEventListener("click", (e) => {
    if (details.open && !details.contains(e.target)) {
      details.removeAttribute("open");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && details.open) {
      details.removeAttribute("open");
      if (summary) summary.focus();
    }
  });
}
