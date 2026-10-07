/**
 * ELECTROCART Small Motions Module (WP8).
 * Thoughtful micro-interactions that earn their place.
 *
 * Rules:
 * - Hairline rules draw their length once when sections enter (editorial only).
 * - Section headings revealed by short opacity and 8px translate once, never replayed.
 * - Content is NEVER hidden from no-JS or print.
 * - Bag count change: text-first polite confirmation in #live-announcer and 2px badge nudge.
 * - Nothing loops except cutout cycle and WebGL idle drift.
 */

let observer = null;

/**
 * Initializes hairline draws and heading reveals on editorial pages.
 */
export function initSmallMotions() {
  if (typeof document === "undefined") return;

  const tier = document.documentElement.dataset.motionTier || "1";
  const isReduced =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (tier === "3" || isReduced) return;

  const isEditorial = document.body && document.body.dataset.layer === "editorial";
  if (!isEditorial) return;

  if (typeof IntersectionObserver === "undefined") return;

  const targets = document.querySelectorAll(
    ".chapter-hairline, .hairline-bottom, .section > h2, .spread h2"
  );

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const el = entry.target;
          if (el.classList.contains("chapter-hairline") || el.classList.contains("hairline-bottom")) {
            el.classList.add("hairline-draw");
          } else {
            el.classList.add("heading-reveal");
          }
          observer.unobserve(el);
        }
      });
    },
    { threshold: 0.15 }
  );

  targets.forEach((el) => observer.observe(el));
}

/**
 * Announces a polite message to screen readers and triggers a gentle 2px bag badge nudge.
 *
 * @param {string} message - e.g. "Added to bag"
 * @param {number} [newCount] - optional updated count number
 */
export function announceBagUpdate(message = "Added to bag", newCount) {
  if (typeof document === "undefined") return;

  // 1. Live Announcer (Aria Live Polite)
  const announcer = document.getElementById("live-announcer");
  if (announcer) {
    announcer.textContent = "";
    setTimeout(() => {
      announcer.textContent = message;
    }, 50);
  }

  // 2. Badge Count Update & 2px Nudge
  const badges = document.querySelectorAll(".header-bag-count, .nav-bag-count");
  badges.forEach((badge) => {
    if (typeof newCount === "number") {
      badge.textContent = String(newCount);
    }
    const tier = document.documentElement.dataset.motionTier || "1";
    if (tier !== "3") {
      badge.classList.remove("bag-count-nudge");
      // Trigger reflow to restart animation
      void badge.offsetWidth;
      badge.classList.add("bag-count-nudge");
    }
  });
}
