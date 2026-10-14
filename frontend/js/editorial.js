/**
 * ELECTROCART Editorial Motion & Interaction Master Entrypoint (Phase 6, WP9).
 * Loaded ONLY on pages with data-layer="editorial" or catalog filter price histogram.
 *
 * Modules included:
 * - Scroller: Lenis smooth scroll synchronized with GSAP ScrollTrigger (Tier 1 fine pointer)
 * - Chapter transitions: Diagonal clip-path wipes and CSS custom property color morphing
 * - Collectible cards: 3D perspective tilt and specular light sheen
 * - Headline cutouts: Cycling photographic inline stamps with circular buffer
 * - Small motions: Hairline rules draw and heading gentle reveals
 * - Price histogram: ARIA dual-thumb stepped log slider with live counts
 * - Hero WebGL scene: Lazy-loaded dynamically on Tier 1 homepage only (Three.js isolated chunk)
 */
import { initScroller } from "./modules/scroller.js";
import { initChapterTransitions } from "./modules/chapter_transitions.js";
import { initCollectibleCards } from "./modules/collectible_cards.js";
import { initHeadlineCutouts } from "./modules/headline_cutouts.js";
import { initSmallMotions } from "./modules/small_motions.js";
import { initPriceHistogram } from "./modules/price_histogram.js";
import { initChapterPinnedStage } from "./modules/chapter_pinned.js";
import { initCategoryGallery } from "./modules/category_gallery.js";
import { initPdpExhibition } from "./modules/pdp_exhibition.js";
import { initMediaSlots } from "./modules/media_slot.js";

function bootstrapEditorial() {
  // 1. Initialize hero entrance choreography (Tier 1 & 2 only, once per session)
  initHeroEntranceChoreography();

  // 2. Initialize editorial scroll and chapter wipes
  initScroller();
  initChapterTransitions();

  // 3. Initialize Hero thumbnail picker & Category Snap Rail arrows (WP3)
  initHeroThumbnailPicker();
  initSnapRailArrows();

  // 4. Initialize Category Index Horizontal Gallery Walk
  initCategoryGallery();

  // 5. Initialize PDP Exhibition Frame Reveal
  initPdpExhibition();

  // 6. Initialize collectible card 3D tilt
  initCollectibleCards();

  // 7. Initialize cycling inline cutouts in hero headline
  initHeadlineCutouts();

  // 8. Initialize section hairline draw & heading reveals
  initSmallMotions();

  // 9. Initialize media slots observer (Tier 1 Desktop video autoplay)
  initMediaSlots();

  // 10. Initialize dual-thumb price histogram (utility enhancement on category detail)
  initPriceHistogram();

  // 11. Initialize Chapter Entrances (WP7: GSAP ScrollTrigger batch)
  initChapterEntrances();
  window.addEventListener("gsap:ready", () => initChapterEntrances());
}

/**
 * Editorial Hero Entrance Choreography (WP1).
 * Runs on editorial pages (homepage), Tier 1 and Tier 2 only, once per session.
 * Skipped on reduced motion or Tier 3.
 */
export function initHeroEntranceChoreography() {
  const heroComp = document.querySelector(".hero-composition");
  if (!heroComp) return;

  const tier = parseInt(document.documentElement.dataset.motionTier || "1", 10);
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Skipped on Tier 3 or prefers-reduced-motion
  if (tier === 3 || isReduced) return;

  // Run once per browser session
  try {
    if (sessionStorage.getItem("hero_entered")) {
      return;
    }
    sessionStorage.setItem("hero_entered", "1");
  } catch (_) {
    // SessionStorage unavailable (e.g. private mode)
  }

  // Hide initial elements using the prep class
  heroComp.classList.add("hero-animate-prep");

  // Safety timeout: reveals everything after 2.0s so content is never stuck
  const safetyTimer = setTimeout(() => {
    heroComp.classList.remove("hero-animate-prep");
    heroComp.classList.remove("hero-animate-run");
  }, 2000);

  // Trigger staged reveal on next animation frames
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      heroComp.classList.add("hero-animate-run");
      setTimeout(() => {
        heroComp.classList.remove("hero-animate-prep");
        clearTimeout(safetyTimer);
      }, 1650);
    });
  });
}

/**
/**
 * Chapter Entrances (WP7).
 * Batches .chapter-shelf-monograph with GSAP ScrollTrigger:
 * y: 24 -> 0, opacity: 0 -> 1, duration: 0.45s, ease: "power2.out", once: true.
 * Final static CSS already has opacity: 1 and transform: none, ensuring full visibility if GSAP is missing.
 */
export function initChapterEntrances() {
  const tier = parseInt(document.documentElement.dataset.motionTier || "1", 10);
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (tier === 3 || isReduced) return;

  const gsapObj = window.gsap || (typeof gsap !== "undefined" ? gsap : null);
  const stObj = window.ScrollTrigger || (typeof ScrollTrigger !== "undefined" ? ScrollTrigger : null);
  if (!gsapObj || !stObj) return;

  try {
    gsapObj.registerPlugin(stObj);
    stObj.config({ syncInterval: 99999999 });
    const elements = document.querySelectorAll(".chapter-shelf-monograph");
    if (!elements.length) return;

    stObj.batch(".chapter-shelf-monograph", {
      onEnter: (batch) => {
        gsapObj.from(batch, {
          y: 24,
          opacity: 0,
          duration: 0.45,
          ease: "power2.out",
          stagger: 0.12,
          overwrite: true,
        });
      },
      once: true,
    });
  } catch (err) {
    console.warn("GSAP chapter entrances init error:", err);
  }
}

export function initHeroThumbnailPicker() {
  const pickerBtns = document.querySelectorAll(".hero-thumb-btn");
  const plateSlot = document.getElementById("hero-plate-slot");
  if (!pickerBtns.length || !plateSlot) return;

  const mainImg = plateSlot.querySelector(".plate-img");
  const mainLink = plateSlot.querySelector("a[href*='/p/']");
  const nameEl = plateSlot.querySelector(".plate-name");
  const priceEl = plateSlot.querySelector(".plate-price");
  const catEl = plateSlot.querySelector(".plate-category");

  pickerBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      pickerBtns.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");

      const title = btn.dataset.heroTitle;
      const url = btn.dataset.heroUrl;
      const price = btn.dataset.heroPrice;
      const img = btn.dataset.heroImg;
      const category = btn.dataset.heroCategory;

      if (mainImg && img) mainImg.src = img;
      if (mainLink && url) mainLink.href = url;
      if (nameEl && title) nameEl.textContent = title;
      if (priceEl && price) priceEl.textContent = price;
      if (catEl && category) catEl.textContent = category;
    });
  });
}

export function initSnapRailArrows() {
  const prevBtn = document.getElementById("snap-rail-prev");
  const nextBtn = document.getElementById("snap-rail-next");
  const rail = document.getElementById("category-snap-rail");
  if (!rail) return;

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      rail.scrollBy({ left: -320, behavior: "smooth" });
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      rail.scrollBy({ left: 320, behavior: "smooth" });
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrapEditorial);
} else {
  bootstrapEditorial();
}
