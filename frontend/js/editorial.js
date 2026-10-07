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

function bootstrapEditorial() {
  // 1. Initialize editorial scroll and chapter wipes
  initScroller();
  initChapterTransitions();

  // 2. Initialize collectible card 3D tilt
  initCollectibleCards();

  // 3. Initialize cycling inline cutouts in hero headline
  initHeadlineCutouts();

  // 4. Initialize section hairline draw & heading reveals
  initSmallMotions();

  // 5. Initialize dual-thumb price histogram (utility enhancement on category detail)
  initPriceHistogram();

  // 6. Initialize WebGL dynamic loader for homepage hero plate
  setupHeroWebGLLoader();
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

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootstrapEditorial);
} else {
  bootstrapEditorial();
}
