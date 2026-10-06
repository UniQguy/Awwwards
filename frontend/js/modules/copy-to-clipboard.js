/**
 * Non-intrusive copy to clipboard with inline polite confirmation.
 */
export function initCopyToClipboard() {
  const buttons = document.querySelectorAll("[data-copy-text]");
  buttons.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const textToCopy = btn.getAttribute("data-copy-text");
      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
        const originalText = btn.textContent;
        btn.textContent = "Copied to clipboard";
        btn.setAttribute("aria-live", "polite");
        setTimeout(() => {
          btn.textContent = originalText;
        }, 2000);
      } catch (err) {
        // Fallback or silent no-op
      }
    });
  });
}
