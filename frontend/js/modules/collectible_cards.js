/**
 * ELECTROCART Collectible Card Tilt Module (WP4).
 * Technique H: 3D perspective tilt with specular glare sweep on the card mat.
 *
 * Rules:
 * - Only active on Tier 1, fine pointer, hover-capable devices.
 * - Max tilt ~6 degrees, perspective 1000px.
 * - Specular sweep gradient on the mat, never on the photo.
 * - Eased back to flat on leave, rAF-throttled, will-change only while active.
 * - Keyboard focus shows a gentle lift, never tilt.
 * - Touch devices and Tier 2/3: flat card with 1px border shift.
 * - Never blocks the link click. Zero layout shift.
 */

/**
 * Pure calculation for tilt angles and specular glare position.
 *
 * @param {DOMRect} rect - Bounding client rect of card
 * @param {number} clientX - Pointer X
 * @param {number} clientY - Pointer Y
 * @param {number} [maxTilt=6] - Maximum rotation angle in degrees
 * @returns {{rotateX: number, rotateY: number, glareX: number, glareY: number, glareOpacity: number}}
 */
export function calculateTilt(rect, clientX, clientY, maxTilt = 6) {
  if (!rect || rect.width <= 0 || rect.height <= 0) {
    return resetTilt();
  }

  // Clamped normalized position [0, 1] relative to card
  const rawX = (clientX - rect.left) / rect.width;
  const rawY = (clientY - rect.top) / rect.height;
  const clampedX = Math.max(0, Math.min(1, rawX));
  const clampedY = Math.max(0, Math.min(1, rawY));

  // Offset from center [-1, 1]
  const dx = (clampedX - 0.5) * 2;
  const dy = (clampedY - 0.5) * 2;

  // Rotation angles (pitch and yaw)
  const rotateX = parseFloat((-dy * maxTilt).toFixed(2));
  const rotateY = parseFloat((dx * maxTilt).toFixed(2));

  // Specular glare coords on mat
  const glareX = parseFloat((clampedX * 100).toFixed(1));
  const glareY = parseFloat((clampedY * 100).toFixed(1));

  // Glare opacity proportional to offset distance from center
  const dist = Math.sqrt(dx * dx + dy * dy);
  const glareOpacity = parseFloat(Math.min(0.25, dist * 0.18).toFixed(3));

  return { rotateX, rotateY, glareX, glareY, glareOpacity };
}

/**
 * Returns neutral reset values for card at rest.
 *
 * @returns {{rotateX: number, rotateY: number, glareX: number, glareY: number, glareOpacity: number}}
 */
export function resetTilt() {
  return {
    rotateX: 0,
    rotateY: 0,
    glareX: 50,
    glareY: 50,
    glareOpacity: 0,
  };
}

let activeCardCleanups = [];

/**
 * Initializes tilt interactions on all [data-tilt-card] elements.
 */
export function initCollectibleCards() {
  teardownCollectibleCards();

  if (typeof document === "undefined" || typeof window === "undefined") return;

  // Strict Tier 1 guard
  const tier = document.documentElement.dataset.motionTier;
  if (tier !== "1") return;

  // Strict Fine pointer / Hover-capable guard
  const isFine = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  if (!isFine) return;

  const cards = document.querySelectorAll("[data-tilt-card]");
  cards.forEach((card) => {
    let rafId = null;
    let isHovering = false;
    let targetCoords = null;

    function onPointerEnter() {
      isHovering = true;
      card.style.willChange = "transform";
      card.classList.add("is-tilting");
    }

    function onPointerMove(e) {
      if (!isHovering) return;
      targetCoords = { clientX: e.clientX, clientY: e.clientY };

      if (!rafId) {
        rafId = window.requestAnimationFrame(() => {
          if (!isHovering || !targetCoords) {
            rafId = null;
            return;
          }
          const rect = card.getBoundingClientRect();
          const tilt = calculateTilt(rect, targetCoords.clientX, targetCoords.clientY, 6);

          card.style.setProperty("--tilt-rx", `${tilt.rotateX}deg`);
          card.style.setProperty("--tilt-ry", `${tilt.rotateY}deg`);
          card.style.setProperty("--tilt-glare-x", `${tilt.glareX}%`);
          card.style.setProperty("--tilt-glare-y", `${tilt.glareY}%`);
          card.style.setProperty("--tilt-glare-opacity", String(tilt.glareOpacity));

          rafId = null;
        });
      }
    }

    function onPointerLeave() {
      isHovering = false;
      targetCoords = null;
      if (rafId) {
        window.cancelAnimationFrame(rafId);
        rafId = null;
      }

      card.classList.remove("is-tilting");
      card.style.willChange = "auto";

      const rest = resetTilt();
      card.style.setProperty("--tilt-rx", `${rest.rotateX}deg`);
      card.style.setProperty("--tilt-ry", `${rest.rotateY}deg`);
      card.style.setProperty("--tilt-glare-x", `${rest.glareX}%`);
      card.style.setProperty("--tilt-glare-y", `${rest.glareY}%`);
      card.style.setProperty("--tilt-glare-opacity", String(rest.glareOpacity));
    }

    card.addEventListener("pointerenter", onPointerEnter, { passive: true });
    card.addEventListener("pointermove", onPointerMove, { passive: true });
    card.addEventListener("pointerleave", onPointerLeave, { passive: true });

    activeCardCleanups.push(() => {
      card.removeEventListener("pointerenter", onPointerEnter);
      card.removeEventListener("pointermove", onPointerMove);
      card.removeEventListener("pointerleave", onPointerLeave);
      if (rafId) window.cancelAnimationFrame(rafId);
      card.classList.remove("is-tilting");
      card.style.willChange = "auto";
    });
  });

  window.addEventListener("motiontierchange", handleTiltTierChange);
}

/**
 * Tears down all active card listeners and animation loops.
 */
export function teardownCollectibleCards() {
  activeCardCleanups.forEach((cleanup) => cleanup());
  activeCardCleanups = [];
  if (typeof window !== "undefined") {
    window.removeEventListener("motiontierchange", handleTiltTierChange);
  }
}

function handleTiltTierChange(event) {
  const tier = event?.detail?.tier;
  if (tier === 1) {
    initCollectibleCards();
  } else {
    teardownCollectibleCards();
  }
}
