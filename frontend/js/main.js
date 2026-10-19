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
import { initMediaSlots } from "./modules/media_slot.js";
import { initRecentlyViewed } from "./modules/recently-viewed.js";
import { initPincodeChecker } from "./modules/pincode_checker.js";

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

function initImageEntryFadeAndLift() {
  const tier = document.documentElement.dataset.motionTier || "1";
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (tier === "3" || isReduced) return;

  const images = document.querySelectorAll(".plate-mat-img, .product-plate img, .hero-plate-slot img, .product-frame-img");
  images.forEach((img) => {
    if (img.complete && img.naturalWidth > 0) return;

    img.style.opacity = "0";
    img.style.transform = "translateY(8px)";
    img.style.transition = "opacity 240ms ease-out, transform 240ms cubic-bezier(0.22, 1, 0.36, 1)";

    let revealed = false;
    const reveal = () => {
      if (revealed) return;
      revealed = true;
      img.style.opacity = "1";
      img.style.transform = "translateY(0)";
    };

    const timer = setTimeout(reveal, 200);

    if (typeof img.decode === "function") {
      img.decode().then(() => {
        clearTimeout(timer);
        reveal();
      }).catch(() => {
        clearTimeout(timer);
        reveal();
      });
    } else {
      img.addEventListener("load", () => {
        clearTimeout(timer);
        reveal();
      }, { once: true });
    }
  });
}

function initCardViewTransitions() {
  document.addEventListener("click", (e) => {
    const link = e.target.closest("a[href*='/p/']");
    if (!link) return;
    const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (isReduced) return;

    const card = link.closest(".plate-collectible, .product-card, .cart-line-item");
    if (card) {
      const img = card.querySelector("img");
      if (img) {
        img.style.viewTransitionName = "product-plate";
      }
    }
  });
}

function initHorizontalFilters() {
  document.addEventListener("change", (e) => {
    const target = e.target;
    if (
      target.matches(".horizontal-filter-select, #filter-brand, #filter-sort") ||
      target.matches(".horizontal-filter-group input[type='checkbox']")
    ) {
      if (target.form) {
        target.form.submit();
      }
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
  initImageEntryFadeAndLift();
  initCardViewTransitions();
  initMediaSlots();
  initRecentlyViewed();
  initPincodeChecker();
  initHorizontalFilters();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrap);
} else {
  bootstrap();
}
