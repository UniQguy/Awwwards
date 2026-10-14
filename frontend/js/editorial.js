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

  // 11. Initialize WebGL dynamic loader for homepage hero plate
  setupHeroWebGLLoader();
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
 * Dynamically loads and initializes the Three.js hero WebGL scene ONLY when:
 * - The hero container `#hero-webgl-canvas-container` is present in the DOM
 * - The active motion tier is 1 (full motion)
 * - The hero container is within or near the viewport (IntersectionObserver)
 *
 * In Tier 2, Tier 3, or when JS is disabled, Three.js is NEVER loaded over the network.
 */
function setupHeroWebGLLoader() {
  const container = document.getElementById("hero-webgl-canvas-container");
  const slot = document.getElementById("hero-plate-slot");
  if (!container || !slot) return;

  const currentTier = document.documentElement.dataset.motionTier || "1";
  if (currentTier !== "1") {
    // Strict requirement: Tier 2 and Tier 3 never load the Three.js chunk
    return;
  }

  const imageUrl = slot.dataset.heroImg;
  if (!imageUrl) return;

  if (typeof IntersectionObserver !== "undefined") {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          observer.disconnect();
          loadHeroWebGLModule(container, slot, imageUrl);
        }
      },
      { rootMargin: "250px" }
    );
    observer.observe(container);
  } else {
    loadHeroWebGLModule(container, slot, imageUrl);
  }
}

async function loadHeroWebGLModule(container, slot, imageUrl) {
  try {
    const { initHeroWebGL, pauseHeroWebGL, resumeHeroWebGL, teardownHeroWebGL } = await import(
      "./modules/hero_webgl.js"
    );

    // Read world background color from computed style or fallback
    let worldBg = "#F5F2EB";
    try {
      const computed = getComputedStyle(document.body).getPropertyValue("--world-bg").trim();
      if (computed && computed.startsWith("#")) {
        worldBg = computed;
      }
    } catch (_) {}

    const ctx = initHeroWebGL(container, imageUrl, worldBg);
    if (!ctx) return;

    // Pause rendering when document/tab is hidden
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        pauseHeroWebGL();
      } else {
        resumeHeroWebGL();
      }
    });

    // Pause rendering when hero container is completely scrolled offscreen
    if (typeof IntersectionObserver !== "undefined") {
      const heroVis = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            resumeHeroWebGL();
          } else {
            pauseHeroWebGL();
          }
        },
        { threshold: 0.05 }
      );
      heroVis.observe(container);
    }

    // Teardown WebGL immediately if motion tier changes away from Tier 1
    window.addEventListener("motiontierchange", (e) => {
      const newTier = e.detail && e.detail.tier;
      if (newTier !== 1) {
        teardownHeroWebGL();
      }
    });
  } catch (err) {
    console.warn("Failed to dynamically load Hero WebGL module, remaining on CSS presentation:", err);
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
