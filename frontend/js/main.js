/**
 * ELECTROCART Frontend Master Entrypoint.
 * Progressive enhancements only. All ecommerce flows function 100% without JS.
 */
import "../css/main.css";
import { initMenuPanel } from "./modules/menu-panel.js";
import { initSearchSheet } from "./modules/search-sheet.js";
import { initFilterSheet } from "./modules/filter-sheet.js";
import { initQuantityStepper } from "./modules/quantity-stepper.js";
import { initCopyToClipboard } from "./modules/copy-to-clipboard.js";
import { initImageFallback } from "./modules/image-fallback.js";
import { initHeaderScroll } from "./modules/header-scroll.js";
import { initMessagesDismiss } from "./modules/messages-dismiss.js";
import { initFetchForms } from "./modules/fetch-forms.js";
import { initStickyPurchaseBar } from "./modules/sticky-purchase-bar.js";
import { initSearchSuggest } from "./modules/search-suggest.js";
import { initMotionTier, initMotionToggleButton } from "./modules/capability.js";

function initPasswordToggle() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-password-toggle], .password-toggle-btn");
    if (!btn) return;
    const group = btn.closest(".password-input-group");
    if (!group) return;
    const input = group.querySelector("input");
    if (!input) return;
    if (input.type === "password") {
      input.type = "text";
      btn.setAttribute("aria-pressed", "true");
      btn.textContent = "Hide";
    } else {
      input.type = "password";
      btn.setAttribute("aria-pressed", "false");
      btn.textContent = "Show";
    }
  });
}

function bootstrap() {
  initMotionTier();
  initMotionToggleButton();
  initMenuPanel();
  initSearchSheet();
  initSearchSuggest();
  initFilterSheet();
  initQuantityStepper();
  initCopyToClipboard();
  initImageFallback();
  initHeaderScroll();
  initMessagesDismiss();
  initFetchForms();
  initStickyPurchaseBar();
  initPasswordToggle();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
