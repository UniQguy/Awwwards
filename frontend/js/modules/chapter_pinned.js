/**
 * ELECTROCART Act 3 Chapter Pinned Stage Module (WP1).
 * Pins the featured chapter stage on Tier 1 desktop (fine pointer, not reduced motion)
 * for 2.2 viewport heights while the lead plate remains anchored and surrounding narrative slides into view.
 *
 * Tier 2/3/mobile/touch: unpinned, native vertical flow.
 * Keyboard navigation: unblocked focus navigation (Tab jumps scroll target into view).
 */

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let pinnedTriggers = [];
let focusListeners = [];

export function initChapterPinnedStage() {
  teardownChapterPinnedStage();

  if (typeof window === "undefined" || typeof document === "undefined") return;

  const tier = document.documentElement.dataset.motionTier || "1";
  const isFine = window.matchMedia("(pointer: fine)").matches;
  const isReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isDesktop = window.innerWidth >= 1024;

  // Strict guard: Tier 1, desktop >= 1024px, fine pointer, not reduced motion
  if (tier !== "1" || !isFine || isReduced || !isDesktop) {
    return;
  }

  const chapters = document.querySelectorAll(".chapter-spread");
  if (!chapters.length) return;

  try {
    gsap.registerPlugin(ScrollTrigger);

    chapters.forEach((chapter) => {
      const leadSlot = chapter.querySelector(".chapter-lead-slot");
      const stackSlot = chapter.querySelector(".chapter-stack-slot");
      const textCol = chapter.querySelector(".chapter-text-col");

      // Timeline scrubbed over 120% scroll distance (pins for 2.2 viewport heights total)
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: chapter,
          pin: true,
          start: "top top",
          end: "+=120%",
          scrub: 0.5,
          anticipatePin: 1,
          invalidateOnRefresh: true,
        },
      });

      // Lead slot stays anchored, satellite stack slides smoothly into view
      if (stackSlot) {
        tl.fromTo(
          stackSlot,
          { y: 32, opacity: 0.8 },
          { y: 0, opacity: 1, duration: 0.6, ease: "power1.out" },
          0
        );
      }

      if (textCol) {
        tl.fromTo(
          textCol,
          { opacity: 0.9 },
          { opacity: 1, duration: 0.4, ease: "power1.out" },
          0
        );
      }

      if (tl.scrollTrigger) {
        pinnedTriggers.push(tl.scrollTrigger);
      }

      // Tab key jumps unblocked: ensure focused interactive elements are scrolled into view
      const onFocusIn = (e) => {
        const el = e.target;
        if (el && typeof el.getBoundingClientRect === "function") {
          const rect = el.getBoundingClientRect();
          if (rect.top < 0 || rect.bottom > window.innerHeight) {
            el.scrollIntoView({ block: "nearest", behavior: "auto" });
          }
        }
      };
      chapter.addEventListener("focusin", onFocusIn);
      focusListeners.push({ target: chapter, handler: onFocusIn });
    });
  } catch (err) {
    console.warn("Failed to initialize chapter pinned stage:", err);
    teardownChapterPinnedStage();
  }

  // React to resize and tier change
  window.addEventListener("resize", handleResize);
  window.addEventListener("motiontierchange", handleTierChange);
}

function handleResize() {
  if (window.innerWidth < 1024 && pinnedTriggers.length > 0) {
    teardownChapterPinnedStage();
  } else if (window.innerWidth >= 1024 && pinnedTriggers.length === 0) {
    initChapterPinnedStage();
  }
}

function handleTierChange(e) {
  const tier = e?.detail?.tier;
  if (tier !== 1) {
    teardownChapterPinnedStage();
  } else {
    initChapterPinnedStage();
  }
}

export function teardownChapterPinnedStage() {
  pinnedTriggers.forEach((st) => {
    try {
      st.kill(true); // reset pinned element styles
    } catch (_) {}
  });
  pinnedTriggers = [];

  focusListeners.forEach(({ target, handler }) => {
    try {
      target.removeEventListener("focusin", handler);
    } catch (_) {}
  });
  focusListeners = [];

  window.removeEventListener("resize", handleResize);
  window.removeEventListener("motiontierchange", handleTierChange);
}
