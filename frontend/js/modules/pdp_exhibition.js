/**
 * ELECTROCART PDP Exhibition Frame Reveal Module (WP1).
 * Features:
 * - Exhibition plate expands gently on entrance (clip-path inset 8% -> 0%, 500ms, Tier 1-2).
 * - Spec table hairline draws across (0% to 100% width) on entrance.
 * - Thumbnail strip interaction if multiple media items are present.
 * - Skipped on Tier 3 / prefers-reduced-motion. Safety timeout clears all inline clip-paths.
 */

export function initPdpExhibition() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  const plate = document.querySelector(".product-frame-mat");
  if (!plate) return;

  const tier = document.documentElement.dataset.motionTier || "1";
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Secondary thumbnail switching (available on all tiers)
  setupThumbnailStrip();

  if (tier === "3" || isReduced) {
    return;
  }

  // Tier 1 & 2 Entrance Choreography
  plate.classList.add("plate-reveal-prep");

  const safetyTimer = setTimeout(() => {
    plate.classList.remove("plate-reveal-prep");
    plate.classList.remove("plate-reveal-run");
  }, 1800);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      plate.classList.add("plate-reveal-run");
      setTimeout(() => {
        plate.classList.remove("plate-reveal-prep");
        plate.classList.remove("plate-reveal-run");
        clearTimeout(safetyTimer);
      }, 600);
    });
  });

  // Specs hairline rule draw
  setupSpecsHairline();
}

function setupThumbnailStrip() {
  const thumbs = document.querySelectorAll(".product-thumb-btn");
  const mainImg = document.querySelector(".product-frame-img");
  if (!thumbs.length || !mainImg) return;

  thumbs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const fullSrc = btn.dataset.fullSrc;
      if (!fullSrc) return;

      thumbs.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");

      mainImg.src = fullSrc;
    });
  });
}

function setupSpecsHairline() {
  const specsHeading = document.getElementById("specs-heading");
  const specTable = document.querySelector(".spec-table-wrapper");
  if (!specsHeading || !specTable) return;

  if (typeof IntersectionObserver === "undefined") return;

  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          specTable.classList.add("spec-rule-drawn");
          obs.disconnect();
        }
      });
    },
    { threshold: 0.2 }
  );

  obs.observe(specsHeading);
}
