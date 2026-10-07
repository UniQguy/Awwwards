/**
 * ELECTROCART Chapter Transitions Module (WP3).
 * Technique E (Color Worlds) & Signature Diagonal Clip-Path Wipe.
 *
 * Rules:
 * - Each chapter section keeps its own data-world.
 * - As a chapter enters, the page-level chrome shifts to that chapter's accent via CSS @property.
 * - Diagonal wipe sweeps across at the seam between chapters:
 *     Tier 1: GSAP ScrollTrigger scrubbed polygon.
 *     Tier 2: CSS keyframe clip-path transition triggered by IntersectionObserver.
 *     Tier 3 / Reduced Motion: 150ms opacity crossfade, or instant.
 * - Aria-hidden and pointer-events: none.
 */

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let currentActiveWorld = null;
let scrollTriggers = [];
let intersectionObservers = [];

/**
 * Initializes chapter transitions and signature diagonal wipes.
 */
export function initChapterTransitions() {
  if (typeof document === "undefined") return;

  const chapters = document.querySelectorAll(".spread[data-world]");
  if (!chapters.length) return;

  // 1. Technique E: Color World Morph on Scroll
  setupWorldColorMorph(chapters);

  // 2. Diagonal Wipe Transitions
  setupDiagonalWipes(chapters);

  // 3. React to tier changes
  window.addEventListener("motiontierchange", handleTierChange);
}

/**
 * Monitors chapter visibility to morph the page-level chrome to the active world.
 *
 * @param {NodeList} chapters
 */
export function setupWorldColorMorph(chapters) {
  if (typeof IntersectionObserver === "undefined") return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const world = entry.target.dataset.world;
          if (world && world !== currentActiveWorld) {
            currentActiveWorld = world;
            if (document.body) {
              document.body.dataset.world = world;
            }
          }
        }
      });
    },
    {
      threshold: 0.35,
      rootMargin: "-10% 0px -10% 0px",
    }
  );

  chapters.forEach((ch) => observer.observe(ch));
  intersectionObservers.push(observer);
}

/**
 * Configures the signature diagonal wipe according to the active motion tier.
 *
 * @param {NodeList} chapters
 */
export function setupDiagonalWipes(chapters) {
  teardownWipes();

  const tier = parseInt(document.documentElement.dataset.motionTier || "1", 10);
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (tier === 3 || isReduced) {
    // Tier 3 / reduced motion: static, no clip-path animation
    return;
  }

  chapters.forEach((section) => {
    const wipe = section.querySelector(".chapter-wipe");
    if (!wipe) return;

    if (tier === 1) {
      // Tier 1: Scrubbed GSAP ScrollTrigger polygon wipe
      try {
        gsap.registerPlugin(ScrollTrigger);

        const tween = gsap.fromTo(
          wipe,
          {
            clipPath: "polygon(0 0, 0 0, 0 100%, 0 100%)",
            opacity: 0.85,
          },
          {
            clipPath: "polygon(100% 0, 100% 0, 100% 100%, 100% 100%)",
            opacity: 0,
            ease: "none",
            scrollTrigger: {
              trigger: section,
              start: "top 85%",
              end: "top 35%",
              scrub: 0.5,
              onLeave: () => {
                wipe.style.opacity = "0";
              },
            },
          }
        );

        if (tween.scrollTrigger) {
          scrollTriggers.push(tween.scrollTrigger);
        }
      } catch (err) {
        // Fallback to Tier 2 on error
        setupTier2Wipe(section, wipe);
      }
    } else if (tier === 2) {
      // Tier 2: CSS keyframe clip-path transition triggered by IntersectionObserver
      setupTier2Wipe(section, wipe);
    }
  });
}

/**
 * Tier 2 CSS Keyframe clip-path wipe triggered by IntersectionObserver.
 *
 * @param {Element} section
 * @param {Element} wipe
 */
function setupTier2Wipe(section, wipe) {
  if (typeof IntersectionObserver === "undefined") return;

  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          wipe.classList.add("chapter-wipe--active");
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  obs.observe(section);
  intersectionObservers.push(obs);
}

/**
 * Tears down all ScrollTrigger and IntersectionObserver wipe instances.
 */
export function teardownWipes() {
  scrollTriggers.forEach((st) => {
    try {
      st.kill();
    } catch (_) {}
  });
  scrollTriggers = [];

  intersectionObservers.forEach((obs) => {
    try {
      obs.disconnect();
    } catch (_) {}
  });
  intersectionObservers = [];
}

/**
 * Reacts to motion tier changes.
 *
 * @param {CustomEvent} event
 */
function handleTierChange() {
  const chapters = document.querySelectorAll(".spread[data-world]");
  if (chapters.length) {
    setupDiagonalWipes(chapters);
  }
}
