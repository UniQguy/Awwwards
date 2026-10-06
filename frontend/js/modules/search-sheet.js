/**
 * Mobile search dialog sheet handler.
 */
export function initSearchSheet() {
  const trigger = document.querySelector("[data-open-search]");
  const dialog = document.querySelector("#search-dialog");
  if (!trigger || !dialog) return;

  const closeBtn = dialog.querySelector("[data-close-search]");
  const input = dialog.querySelector("input[type='search']");

  trigger.addEventListener("click", () => {
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
      if (input) input.focus();
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
