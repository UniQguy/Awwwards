/**
 * ELECTROCART Category Index Horizontal Gallery Walk Module (WP1).
 * Smooth wheel-driven horizontal monograph walk on Tier 1 desktop (fine pointer, not reduced motion).
 *
 * Tier 2/3/mobile/touch: generous vertical card stacks.
 * Unblocked keyboard navigation: Tab focus scrolls active card into view.
 * Interactive progress bar: visual scrub indicator that supports clicking to seek.
 */

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let galleryTrigger = null;
let progressBarEl = null;
let focusHandler = null;

export function initCategoryGallery() {
  teardownCategoryGallery();

  if (typeof window === "undefined" || typeof document === "undefined") return;

  const container = document.querySelector(".category-index-flow");
  if (!container) return;

  const spreads = container.querySelectorAll(".category-row-spread");
  if (spreads.length < 2) return;

  const tier = document.documentElement.dataset.motionTier || "1";
  const isFine = window.matchMedia("(pointer: fine)").matches;
  const isReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isDesktop = window.innerWidth >= 1024;

  // Tier 1 Desktop fine-pointer path only
  if (tier !== "1" || !isFine || isReduced || !isDesktop) {
    return;
  }

  try {
    gsap.registerPlugin(ScrollTrigger);

    container.classList.add("is-horizontal-gallery");
    document.body.classList.add("is-horizontal-gallery-active");

    const totalSpreads = spreads.length;

    // Build or attach interactive progress bar
    progressBarEl = setupProgressBar(totalSpreads);

    const fillEl = progressBarEl.querySelector(".category-gallery-progress-fill");
    const numEl = progressBarEl.querySelector(".category-gallery-progress-num");

    const scrollDistance = window.innerWidth * (totalSpreads - 1) * 0.8;

    const tween = gsap.to(spreads, {
      xPercent: -100 * (totalSpreads - 1),
      ease: "none",
      scrollTrigger: {
        trigger: container,
        pin: true,
        scrub: 0.5,
        snap: 1 / (totalSpreads - 1),
        start: "top top",
        end: () => `+=${scrollDistance}`,
        invalidateOnRefresh: true,
        onUpdate: (self) => {
          const progress = self.progress;
          const currentIdx = Math.min(totalSpreads, Math.floor(progress * totalSpreads * 0.999) + 1);
          if (fillEl) fillEl.style.width = `${(progress * 100).toFixed(1)}%`;
          if (numEl) numEl.textContent = `${String(currentIdx).padStart(2, "0")} / ${String(totalSpreads).padStart(2, "0")}`;

          // Update active world color for page chrome
          const activeSpread = spreads[currentIdx - 1];
          if (activeSpread && activeSpread.dataset.world) {
            document.body.dataset.world = activeSpread.dataset.world;
          }
        },
      },
    });

    galleryTrigger = tween.scrollTrigger;

    // Interactive clicking on progress bar
    progressBarEl.addEventListener("click", handleProgressBarClick);

    // Unblocked keyboard tab navigation
    focusHandler = (e) => {
      const target = e.target;
      const spreadIndex = Array.from(spreads).findIndex((s) => s.contains(target));
      if (spreadIndex >= 0 && galleryTrigger) {
        const targetProgress = spreadIndex / (totalSpreads - 1);
        const targetScroll = galleryTrigger.start + targetProgress * (galleryTrigger.end - galleryTrigger.start);
        window.scrollTo({ top: targetScroll, behavior: "smooth" });
      }
    };
    container.addEventListener("focusin", focusHandler);
  } catch (err) {
    console.warn("Failed to initialize Category Gallery:", err);
    teardownCategoryGallery();
  }

  window.addEventListener("resize", handleResize);
  window.addEventListener("motiontierchange", handleTierChange);
}

function setupProgressBar(total) {
  let el = document.getElementById("category-gallery-progress");
  if (!el) {
    el = document.createElement("div");
    el.id = "category-gallery-progress";
    el.className = "category-gallery-progress";
    el.setAttribute("role", "progressbar");
    el.setAttribute("aria-label", "Catalogue gallery walk progress");
    el.innerHTML = `
      <div class="category-gallery-progress-bar">
        <div class="category-gallery-progress-fill"></div>
      </div>
      <span class="category-gallery-progress-num">01 / ${String(total).padStart(2, "0")}</span>
    `;
    document.body.appendChild(el);
  }
  return el;
}

function handleProgressBarClick(e) {
  if (!galleryTrigger) return;
  const bar = progressBarEl.querySelector(".category-gallery-progress-bar");
  if (!bar) return;
  const rect = bar.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const fraction = Math.max(0, Math.min(1, clickX / rect.width));
  const targetScroll = galleryTrigger.start + fraction * (galleryTrigger.end - galleryTrigger.start);
  window.scrollTo({ top: targetScroll, behavior: "smooth" });
}

function handleResize() {
  if (window.innerWidth < 1024 && galleryTrigger) {
    teardownCategoryGallery();
  } else if (window.innerWidth >= 1024 && !galleryTrigger) {
    initCategoryGallery();
  }
}

function handleTierChange(e) {
  const tier = e?.detail?.tier;
  if (tier !== 1) {
    teardownCategoryGallery();
  } else {
    initCategoryGallery();
  }
}

export function teardownCategoryGallery() {
  if (galleryTrigger) {
    try {
      galleryTrigger.kill(true);
    } catch (_) {}
    galleryTrigger = null;
  }

  const container = document.querySelector(".category-index-flow");
  if (container) {
    container.classList.remove("is-horizontal-gallery");
    if (focusHandler) {
      container.removeEventListener("focusin", focusHandler);
      focusHandler = null;
    }
    const spreads = container.querySelectorAll(".category-row-spread");
    spreads.forEach((s) => {
      gsap.set(s, { clearProps: "all" });
    });
  }

  document.body.classList.remove("is-horizontal-gallery-active");

  if (progressBarEl) {
    progressBarEl.removeEventListener("click", handleProgressBarClick);
    progressBarEl.remove();
    progressBarEl = null;
  }

  window.removeEventListener("resize", handleResize);
  window.removeEventListener("motiontierchange", handleTierChange);
}
