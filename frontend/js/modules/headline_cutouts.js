/**
 * ELECTROCART Cycling Inline Headline Cutouts Module (WP5).
 * Technique A: Cycling hero inline product cutouts.
 *
 * Rules:
 * - Active on Tier 1 and Tier 2.
 * - Staggered cycling (6 to 9s per cutout), 2 to 4px gentle float + crossfade.
 * - Paused while tab is hidden, when offscreen, on hover/focus in hero, and under reduced motion.
 * - Preloads next image one step ahead.
 * - Uses server-rendered #hero-cutouts-data (json_script). Zero extra HTTP requests.
 * - DOM sentence text never changes; cutouts remain aria-hidden.
 * - Tier 3: Static.
 */

/**
 * Pure check to determine whether cutouts should cycle in current state.
 *
 * @param {Object} state
 * @param {string|number} state.tier - Current motion tier
 * @param {boolean} state.isHidden - document.hidden
 * @param {boolean} state.isIntersecting - Hero visible in viewport
 * @param {boolean} state.isHovered - User hovering or focusing inside hero
 * @param {boolean} state.isReducedMotion - prefers-reduced-motion active
 * @returns {boolean}
 */
export function canCycleCutouts({ tier, isHidden, isIntersecting, isHovered, isReducedMotion }) {
  if (isReducedMotion) return false;
  if (String(tier) === "3") return false;
  if (isHidden) return false;
  if (isHovered) return false;
  if (!isIntersecting) return false;
  return true;
}

/**
 * Pure index increment helper for circular buffer cycling.
 *
 * @param {number} current - Current index
 * @param {number} total - Total items available
 * @param {number} [step=1]
 * @returns {number}
 */
export function getNextCycleIndex(current, total, step = 1) {
  if (!total || total <= 0) return 0;
  return (current + step) % total;
}

let activeIntervals = [];
let heroObserver = null;
let eventListenersCleanups = [];

/**
 * Initializes cycling inline cutouts on the homepage.
 */
export function initHeadlineCutouts() {
  teardownHeadlineCutouts();

  if (typeof document === "undefined") return;

  const dataScript = document.getElementById("hero-cutouts-data");
  if (!dataScript) return;

  let cutoutData = [];
  try {
    cutoutData = JSON.parse(dataScript.textContent || "[]");
  } catch (_) {
    return;
  }

  if (!Array.isArray(cutoutData) || cutoutData.length <= 1) return;

  const heroSection = document.querySelector(".hero-composition");
  const cutoutElements = document.querySelectorAll(".hero-headline .cutout");
  if (!heroSection || !cutoutElements.length) return;

  let isHeroIntersecting = true;
  let isHeroHovered = false;

  // Track hover/focus inside hero to pause animation
  function onHeroEnter() {
    isHeroHovered = true;
  }
  function onHeroLeave() {
    isHeroHovered = false;
  }

  heroSection.addEventListener("pointerenter", onHeroEnter, { passive: true });
  heroSection.addEventListener("pointerleave", onHeroLeave, { passive: true });
  heroSection.addEventListener("focusin", onHeroEnter, { passive: true });
  heroSection.addEventListener("focusout", onHeroLeave, { passive: true });

  eventListenersCleanups.push(() => {
    heroSection.removeEventListener("pointerenter", onHeroEnter);
    heroSection.removeEventListener("pointerleave", onHeroLeave);
    heroSection.removeEventListener("focusin", onHeroEnter);
    heroSection.removeEventListener("focusout", onHeroLeave);
  });

  // Track hero visibility with IntersectionObserver
  if (typeof IntersectionObserver !== "undefined") {
    heroObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        isHeroIntersecting = entry.isIntersecting;
      });
    });
    heroObserver.observe(heroSection);
  }

  // Preload images cache
  const preloadedImages = new Set();
  function preloadImage(url) {
    if (!url || preloadedImages.has(url)) return;
    const img = new Image();
    img.src = url;
    preloadedImages.add(url);
  }

  // In R6 shop floor, headline cutouts serve as static typographic stamps.
  // Recurring setInterval looping decoration is disabled per Rule D and Rule J (idle check).
  cutoutElements.forEach((cutout, cutoutIndex) => {
    const img = cutout.querySelector(".cutout-img");
    if (!img) return;
    if (cutoutData[cutoutIndex] && cutoutData[cutoutIndex].image_url) {
      preloadImage(cutoutData[cutoutIndex].image_url);
    }
  });

  // Listen for motiontierchange
  window.addEventListener("motiontierchange", handleCutoutTierChange);
}

/**
 * Tears down all intervals and observers.
 */
export function teardownHeadlineCutouts() {
  activeIntervals.forEach((id) => {
    clearInterval(id);
    clearTimeout(id);
  });
  activeIntervals = [];

  if (heroObserver) {
    heroObserver.disconnect();
    heroObserver = null;
  }

  eventListenersCleanups.forEach((cleanup) => cleanup());
  eventListenersCleanups = [];

  if (typeof window !== "undefined") {
    window.removeEventListener("motiontierchange", handleCutoutTierChange);
  }
}

function handleCutoutTierChange(e) {
  const tier = e?.detail?.tier;
  if (tier === 3) {
    teardownHeadlineCutouts();
  } else {
    initHeadlineCutouts();
  }
}
