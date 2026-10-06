/**
 * Mobile filter bottom sheet dialog handler.
 * Leverages native HTML5 <dialog> focus trapping and modal semantics.
 */
export function initFilterSheet() {
  const trigger = document.querySelector("[data-open-filters]");
  const dialog = document.querySelector("#filter-dialog");
  if (!trigger || !dialog) return;

  const closeBtn = dialog.querySelector("[data-close-filters]");

  trigger.addEventListener("click", () => {
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      dialog.close();
      trigger.focus();
    });
  }

  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) {
      dialog.close();
      trigger.focus();
    }
  });
}
