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
import { initKineticChapters } from "./modules/kinetic_chapters.js";

function bootstrapEditorial() {
  // 0. Initialize 9-Chapter Kinetic Monograph modules (Phase R8)
  initKineticChapters();
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
  const anatomyPillBtns = document.querySelectorAll(".anatomy-flagship-btn");
  const anatomyChapter = document.getElementById("flagship-anatomy-chapter");

  let flagshipsData = [];
  const scriptDataEl = document.getElementById("hero-flagships-data");
  if (scriptDataEl) {
    try {
      flagshipsData = JSON.parse(scriptDataEl.textContent);
    } catch (_) {}
  }

  const mainImg = plateSlot ? (plateSlot.querySelector(".plate-mat-img") || plateSlot.querySelector(".plate-img")) : null;
  const mainLink = plateSlot ? (plateSlot.querySelector("a.stretched-link") || plateSlot.querySelector("a[href*='/p/']")) : null;
  const exploreBtn = document.getElementById("hero-explore-btn");
  const titleEl = plateSlot ? (plateSlot.querySelector(".plate-title") || plateSlot.querySelector(".card-title")) : null;
  const brandEl = plateSlot ? plateSlot.querySelector(".plate-meta-line span") : null;
  const priceEl = plateSlot ? (plateSlot.querySelector(".price-current") || plateSlot.querySelector(".plate-price")) : null;
  const mrpWrapper = plateSlot ? plateSlot.querySelector(".price-mrp-wrapper") : null;
  const mrpEl = plateSlot ? plateSlot.querySelector(".price-mrp-struck") : null;
  const savingsEl = plateSlot ? plateSlot.querySelector(".badge-savings") : null;
  const captionEl = plateSlot ? plateSlot.querySelector(".plate-caption") : null;

  // Anatomy chapter elements
  const anatomyNameEl = anatomyChapter ? anatomyChapter.querySelector(".anatomy-product-name") : null;
  const anatomyImgEl = anatomyChapter ? anatomyChapter.querySelector(".anatomy-stage-img") : null;
  const anatomyPriceEl = anatomyChapter ? anatomyChapter.querySelector(".anatomy-price-val") : null;
  const anatomyFormEl = anatomyChapter ? document.getElementById("anatomy-add-form") : null;
  const anatomyTabs = anatomyChapter ? anatomyChapter.querySelectorAll(".anatomy-layer-tab") : [];

  function selectFlagship(idx) {
    idx = parseInt(idx, 10);
    if (isNaN(idx) || idx < 0) idx = 0;

    // Update active states on both Chapter 01 thumbnails and Chapter 02 pills
    pickerBtns.forEach((b, i) => {
      if (i === idx) b.classList.add("is-active");
      else b.classList.remove("is-active");
    });

    anatomyPillBtns.forEach((b, i) => {
      if (i === idx) {
        b.classList.add("btn-primary", "is-active");
        b.classList.remove("btn-secondary");
      } else {
        b.classList.remove("btn-primary", "is-active");
        b.classList.add("btn-secondary");
      }
    });

    const data = flagshipsData[idx];
    const btn = pickerBtns[idx];

    const title = data ? data.title : (btn ? (btn.dataset.title || btn.dataset.heroTitle) : "");
    const brand = data ? data.brand : (btn ? btn.dataset.brand : "");
    const url = data ? data.url : (btn ? (btn.dataset.url || btn.dataset.heroUrl) : "");
    const price = data ? data.selling_price : (btn ? (btn.dataset.price || btn.dataset.heroPrice) : "");
    const mrp = data ? data.mrp : (btn ? btn.dataset.mrp : "");
    const savings = data ? data.savings : (btn ? btn.dataset.savings : "");
    const img = data ? data.image : (btn ? (btn.dataset.image || btn.dataset.heroImg) : "");
    const subtitle = data ? (data.category_name || "") : (btn ? (btn.dataset.subtitle || btn.dataset.heroCategory) : "");

    // 1. Update Chapter 01 Hero Card
    if (mainImg && img) {
      mainImg.style.transition = "opacity 140ms ease-out, transform 140ms ease-out";
      mainImg.style.opacity = "0.2";
      mainImg.style.transform = "scale(0.97)";
      setTimeout(() => {
        mainImg.src = img;
        mainImg.alt = title || "";
        mainImg.style.opacity = "1";
        mainImg.style.transform = "scale(1)";
      }, 140);
    }

    if (mainLink && url) mainLink.href = url;
    if (exploreBtn && url) exploreBtn.href = url;
    if (titleEl && title) titleEl.textContent = title;
    if (brandEl && brand) brandEl.textContent = brand;
    if (priceEl && price) priceEl.textContent = price;

    if (mrpWrapper && mrpEl) {
      if (mrp) {
        mrpEl.textContent = mrp;
        mrpWrapper.style.display = "";
      } else {
        mrpWrapper.style.display = "none";
      }
    }

    if (savingsEl) {
      if (savings) {
        savingsEl.textContent = savings;
        savingsEl.style.display = "";
      } else {
        savingsEl.style.display = "none";
      }
    }

    if (captionEl && subtitle) {
      captionEl.textContent = subtitle;
    }

    // 2. Update Chapter 02 Flagship Engineering Anatomy
    if (anatomyNameEl && title) {
      anatomyNameEl.textContent = title;
    }

    if (anatomyImgEl && img) {
      anatomyImgEl.style.transition = "opacity 140ms ease-out, transform 140ms ease-out";
      anatomyImgEl.style.opacity = "0.2";
      setTimeout(() => {
        anatomyImgEl.src = img;
        anatomyImgEl.alt = title || "";
        anatomyImgEl.style.opacity = "1";
      }, 140);
    }

    if (anatomyPriceEl && price) {
      anatomyPriceEl.textContent = price;
    }

    if (anatomyFormEl && data && data.add_to_cart_url) {
      anatomyFormEl.action = data.add_to_cart_url;
    }

    // Update 4 anatomy layers if present in data
    if (data && data.layers && data.layers.length) {
      anatomyTabs.forEach((tab, tIdx) => {
        const layer = data.layers[tIdx];
        if (layer) {
          const numEl = tab.querySelector(".anatomy-tab-num");
          const titleEl2 = tab.querySelector(".anatomy-tab-title");
          const descEl = tab.querySelector(".anatomy-tab-desc");
          if (numEl && layer.num) numEl.textContent = layer.num;
          if (titleEl2 && layer.title) titleEl2.textContent = layer.title;
          if (descEl && layer.desc) descEl.textContent = layer.desc;
        }
      });
    }
  }

  // Bind Chapter 01 thumbnails
  pickerBtns.forEach((btn, idx) => {
    btn.addEventListener("click", () => selectFlagship(idx));
    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectFlagship(idx);
      }
    });
  });

  // Bind Chapter 02 anatomy pills
  anatomyPillBtns.forEach((btn, idx) => {
    btn.addEventListener("click", () => selectFlagship(idx));
    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectFlagship(idx);
      }
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
