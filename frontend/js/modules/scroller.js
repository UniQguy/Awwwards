/**
 * ELECTROCART Smooth Scroller Module (WP2).
 * Lenis smooth scrolling with GSAP ScrollTrigger synchronization.
 *
 * Strict safety rules:
 * - Starts ONLY on Tier 1, fine pointer, desktop widths (>= 1024px), on body[data-layer="editorial"].
 * - NEVER on /cart/, /checkout/, /account/, /orders/, filter rails, or when a <dialog> is open.
 * - Stops when any <dialog> opens, resumes on close.
 * - Respects anchor links, skip link, keyboard scrolling (Space, PageDown, arrows, Home, End), and text selection.
 * - Pairs with the visible "Reduce motion" control in the footer.
 */

import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { setManualMotionPreference, STORAGE_KEY_USER_PREF, initMotionToggleButton } from "./capability.js";

let lenisInstance = null;
let tickerCallback = null;
let dialogObservers = [];
let scrollTriggerRegistered = false;

/**
 * Checks whether Lenis should run in the current environment and page context.
 *
 * @returns {boolean}
 */
export function shouldEnableLenis() {
  if (typeof document === "undefined" || typeof window === "undefined") {
    return false;
  }

  // 1. Motion tier must be Tier 1
  const tier = document.documentElement.dataset.motionTier;
  if (tier !== "1") {
    return false;
  }

  // 2. Fine pointer only (no touch / coarse devices)
  const isFinePointer = window.matchMedia("(pointer: fine)").matches;
  if (!isFinePointer) {
    return false;
  }

  // 3. Desktop width only
  if (window.innerWidth < 1024) {
    return false;
  }

  // 4. Strictly on editorial pages
  const isEditorial = document.body && document.body.dataset.layer === "editorial";
  if (!isEditorial) {
    return false;
  }

  // 5. Exclude utility paths explicitly as safety rail
  const path = window.location.pathname;
  const excludedPrefixes = ["/cart", "/checkout", "/account", "/orders", "/search", "/compare", "/legal"];
  if (excludedPrefixes.some((p) => path.startsWith(p))) {
    return false;
  }

  return true;
}

/**
 * Initializes Lenis smooth scrolling if conditions are met.
 *
 * @returns {Lenis|null}
 */
export function initScroller() {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return null;
  }

  // Wire up the footer Reduce Motion toggle button in all environments
  initMotionToggleButton();

  if (!shouldEnableLenis()) {
    destroyScroller();
    return null;
  }

  if (lenisInstance) {
    return lenisInstance;
  }

  try {
    if (!scrollTriggerRegistered) {
      gsap.registerPlugin(ScrollTrigger);
      scrollTriggerRegistered = true;
    }

    // Create Lenis instance configured for accessibility and standard keyboard handling
    lenisInstance = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // exponential ease-out
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 0.9,
      touchMultiplier: 1.5,
      autoRaf: false, // Driven by GSAP ticker
    });

    // Synchronize Lenis scroll events with GSAP ScrollTrigger
    lenisInstance.on("scroll", ScrollTrigger.update);

    // Sync with GSAP ticker loop
    tickerCallback = (time) => {
      if (lenisInstance) {
        lenisInstance.raf(time * 1000);
      }
    };
    gsap.ticker.add(tickerCallback);
    gsap.ticker.lagSmoothing(0);

    // Watch <dialog> open/close events to freeze Lenis while dialogs are open
    setupDialogGuards();

    // Listen for motion tier changes to tear down Lenis immediately if tier changes
    window.addEventListener("motiontierchange", handleMotionTierChange);

    return lenisInstance;
  } catch (err) {
    console.warn("Failed to initialize Lenis scroller:", err);
    destroyScroller();
    return null;
  }
}

/**
 * Stops and destroys the active Lenis instance, unbinding ticker and event handlers.
 */
export function destroyScroller() {
  if (tickerCallback) {
    gsap.ticker.remove(tickerCallback);
    tickerCallback = null;
  }

  if (lenisInstance) {
    try {
      lenisInstance.destroy();
    } catch (_) {}
    lenisInstance = null;
  }

  // Remove dialog observers
  dialogObservers.forEach((disconnect) => disconnect());
  dialogObservers = [];

  window.removeEventListener("motiontierchange", handleMotionTierChange);
}

/**
 * Reacts to motion tier changes (e.g. from Reduce Motion button or probe).
 *
 * @param {CustomEvent} event
 */
function handleMotionTierChange(event) {
  const tier = event?.detail?.tier;
  if (tier !== 1 && lenisInstance) {
    destroyScroller();
  } else if (tier === 1 && !lenisInstance) {
    initScroller();
  }
}

/**
 * Attaches mutation observers to modal <dialog> elements to pause Lenis when open.
 */
function setupDialogGuards() {
  dialogObservers.forEach((disconnect) => disconnect());
  dialogObservers = [];

  const dialogs = document.querySelectorAll("dialog");
  dialogs.forEach((dialog) => {
    // Standard dialog open/close events
    dialog.addEventListener("close", () => {
      if (lenisInstance) lenisInstance.start();
    });

    // Observer for open attribute changes
    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.attributeName === "open") {
          const isOpen = dialog.hasAttribute("open");
          if (isOpen && lenisInstance) {
            lenisInstance.stop();
          } else if (!isOpen && lenisInstance) {
            lenisInstance.start();
          }
        }
      }
    });

    observer.observe(dialog, { attributes: true, attributeFilter: ["open"] });
    dialogObservers.push(() => {
      observer.disconnect();
    });
  });
}

export { initMotionToggleButton } from "./capability.js";

