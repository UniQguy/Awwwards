/**
 * Dismissible alert message banners.
 */
export function initMessagesDismiss() {
  const dismissButtons = document.querySelectorAll(".alert-dismiss-btn");
  dismissButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        alert.style.transform = "translateY(-4px)";
        setTimeout(() => alert.remove(), 200);
      }
    });
  });
}
