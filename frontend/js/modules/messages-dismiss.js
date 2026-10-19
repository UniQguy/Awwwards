/**
 * Dismissible alert message toast notifications (Phase R10).
 * Capped at 2 toasts max, auto-dismisses in 4000ms.
 */
export function initMessagesDismiss() {
  const container = document.querySelector(".messages-container");
  if (!container) return;

  const alerts = Array.from(container.querySelectorAll(".alert"));
  // Cap at 2: keep latest 2
  if (alerts.length > 2) {
    alerts.slice(0, alerts.length - 2).forEach((al) => al.remove());
  }

  function dismiss(alert) {
    if (!alert || alert.dataset.dismissing) return;
    alert.dataset.dismissing = "true";
    alert.style.opacity = "0";
    alert.style.transform = "translateY(8px) scale(0.96)";
    setTimeout(() => {
      alert.remove();
      if (!container.querySelectorAll(".alert").length) {
        container.remove();
      }
    }, 240);
  }

  container.querySelectorAll(".alert").forEach((alert) => {
    // Auto-dismiss in 4000ms
    const timer = setTimeout(() => dismiss(alert), 4000);

    const btn = alert.querySelector(".alert-dismiss-btn");
    if (btn) {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        clearTimeout(timer);
        dismiss(alert);
      });
    }
  });
}
