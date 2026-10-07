/**
 * ELECTROCART Capability and Motion Tier Selection Module (WP1).
 * Pure and unit-testable capability detection.
 *
 * Tier 1 (Full): WebGL scenes, GSAP scrubbed wipes, Lenis smooth scroll, 3D card tilt.
 * Tier 2 (Lite): CSS transforms and clip-path transitions only, no WebGL, no Lenis.
 * Tier 3 (Static): Zero continuous motion. Opacity crossfades (150ms) for reduced-motion, or instant.
 */

export const STORAGE_KEY_USER_PREF = "electrocart-motion-preference";
export const STORAGE_KEY_SESSION_TIER = "electrocart-motion-tier";

/**
 * Checks WebGL / WebGL2 context availability using a throwaway canvas,
 * and immediately loses the context to release GPU resources.
 *
 * @param {HTMLCanvasElement} [canvas] - Optional canvas for testing
 * @returns {boolean}
 */
export function probeWebGL(canvas) {
  try {
    const el = canvas || (typeof document !== "undefined" ? document.createElement("canvas") : null);
    if (!el) return false;
    const gl = el.getContext("webgl2") || el.getContext("webgl") || el.getContext("experimental-webgl");
    if (!gl) return false;
    const loseExt = gl.getExtension("WEBGL_lose_context");
    if (loseExt && typeof loseExt.loseContext === "function") {
      loseExt.loseContext();
    }
    return true;
  } catch (err) {
    return false;
  }
}

/**
 * Measures requestAnimationFrame frame intervals for ~400ms to detect low-end devices.
 * If median delta > 24ms (i.e. < 40 FPS), indicates GPU/CPU throttling.
 *
 * @param {number} [durationMs=400]
 * @returns {Promise<number>} Median frame delta in milliseconds
 */
export function runFrameProbe(durationMs = 400) {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !window.requestAnimationFrame) {
      return resolve(16.6);
    }
    const deltas = [];
    let lastTime = performance.now();
    const startTime = lastTime;

    function frame(now) {
      const delta = now - lastTime;
      lastTime = now;
      if (delta > 0 && delta < 200) {
        deltas.push(delta);
      }
      if (now - startTime < durationMs) {
        window.requestAnimationFrame(frame);
      } else {
        if (deltas.length === 0) return resolve(16.6);
        deltas.sort((a, b) => a - b);
        const mid = Math.floor(deltas.length / 2);
        const median = deltas.length % 2 === 0 ? (deltas[mid - 1] + deltas[mid]) / 2 : deltas[mid];
        resolve(median);
      }
    }

    window.requestAnimationFrame(frame);
  });
}

/**
 * Pure evaluation function that takes an environment snapshot and computes the motion tier.
 *
 * @param {Object} env
 * @param {string|null} [env.motionDebugParam] - ?motion=1|2|3 from URL when motion debug is enabled
 * @param {string|null} [env.userPreference] - "reduced" or null from localStorage
 * @param {boolean} [env.prefersReducedMotion] - matches (prefers-reduced-motion: reduce)
 * @param {boolean} [env.saveData] - navigator.connection.saveData
 * @param {string} [env.effectiveType] - 'slow-2g' | '2g' | '3g' | '4g'
 * @param {number} [env.deviceMemory] - RAM in GB (e.g. 4, 8)
 * @param {number} [env.hardwareConcurrency] - CPU cores (e.g. 4, 8)
 * @param {boolean} [env.isCoarsePointer] - matches (pointer: coarse)
 * @param {number} [env.viewportWidth] - window.innerWidth
 * @param {boolean} [env.hasWebGL] - WebGL context available
 * @param {number} [env.medianFrameDelta] - median rAF delta from frame probe
 * @returns {number} 1, 2, or 3
 */
export function evaluateCapabilities(env) {
  // 1. Dev override (?motion=1|2|3)
  if (env.motionDebugParam === "1") return 1;
  if (env.motionDebugParam === "2") return 2;
  if (env.motionDebugParam === "3") return 3;

  // 2. User persistent preference: manual "Reduce motion" button
  if (env.userPreference === "reduced") {
    return 3;
  }

  // 3. OS-level prefers-reduced-motion ALWAYS yields Tier 3
  if (env.prefersReducedMotion) {
    return 3;
  }

  // 4. Save-Data mode or slow network yields at most Tier 2
  const isSlowNetwork =
    env.saveData === true ||
    env.effectiveType === "slow-2g" ||
    env.effectiveType === "2g" ||
    env.effectiveType === "3g";

  // 5. Hardware constraints: low memory or low CPU cores
  const isLowSpecHardware =
    (typeof env.deviceMemory === "number" && env.deviceMemory < 4) ||
    (typeof env.hardwareConcurrency === "number" && env.hardwareConcurrency <= 2);

  // 6. Mobile / touch device constraints
  const isMobileOrTouch = env.isCoarsePointer || (typeof env.viewportWidth === "number" && env.viewportWidth < 1024);

  // 7. WebGL capability
  const hasWorkingWebGL = env.hasWebGL !== false;

  // 8. Frame delta performance: median > 24ms means device cannot sustain 40+ FPS
  const isDroppedFrames = typeof env.medianFrameDelta === "number" && env.medianFrameDelta > 24;

  // If any constraint prevents full fidelity, drop to Tier 2
  if (
    isSlowNetwork ||
    isLowSpecHardware ||
    isMobileOrTouch ||
    !hasWorkingWebGL ||
    isDroppedFrames
  ) {
    return 2;
  }

  // High-spec desktop environment with fine pointer, fast connection, WebGL: Full Tier 1
  return 1;
}

/**
 * Collects live browser environment properties.
 *
 * @returns {Object}
 */
export function getLiveEnvironment() {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return {
      prefersReducedMotion: false,
      viewportWidth: 1440,
      hasWebGL: true,
    };
  }

  // Dev override from query param if motion debug enabled on document
  let motionDebugParam = null;
  const isDebugAllowed = document.documentElement.dataset.motionDebug === "true";
  if (isDebugAllowed) {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const m = urlParams.get("motion");
      if (m === "1" || m === "2" || m === "3") {
        motionDebugParam = m;
      }
    } catch (_) {}
  }

  // User persistent preference
  let userPreference = null;
  try {
    userPreference = localStorage.getItem(STORAGE_KEY_USER_PREF);
  } catch (_) {}

  // OS prefers-reduced-motion
  let prefersReducedMotion = false;
  try {
    prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (_) {}

  // Connection info
  const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection || {};
  const saveData = Boolean(conn.saveData);
  const effectiveType = conn.effectiveType || "4g";

  // Device specs
  const deviceMemory = navigator.deviceMemory;
  const hardwareConcurrency = navigator.hardwareConcurrency;

  // Pointer
  let isCoarsePointer = false;
  try {
    isCoarsePointer = window.matchMedia("(pointer: coarse)").matches;
  } catch (_) {}

  // Viewport
  const viewportWidth = window.innerWidth;

  // WebGL
  const hasWebGL = probeWebGL();

  return {
    motionDebugParam,
    userPreference,
    prefersReducedMotion,
    saveData,
    effectiveType,
    deviceMemory,
    hardwareConcurrency,
    isCoarsePointer,
    viewportWidth,
    hasWebGL,
  };
}

/**
 * Initializes and determines the active motion tier.
 * Caches the tier in sessionStorage, sets document attribute, and dispatches CustomEvent.
 *
 * @param {boolean} [skipFrameProbe=false]
 * @returns {Promise<number>} Active tier (1, 2, or 3)
 */
export async function initMotionTier(skipFrameProbe = false) {
  if (typeof document === "undefined") return 3;

  // 1. Check dev override first (never cache dev override in session)
  const isDebugAllowed = document.documentElement.dataset.motionDebug === "true";
  if (isDebugAllowed) {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const m = urlParams.get("motion");
      if (m === "1" || m === "2" || m === "3") {
        const forced = parseInt(m, 10);
        applyMotionTier(forced);
        return forced;
      }
    } catch (_) {}
  }

  // 2. Check cached tier in sessionStorage
  try {
    const cached = sessionStorage.getItem(STORAGE_KEY_SESSION_TIER);
    if (cached === "1" || cached === "2" || cached === "3") {
      const tier = parseInt(cached, 10);
      applyMotionTier(tier);
      return tier;
    }
  } catch (_) {}

  // 3. Collect environment
  const env = getLiveEnvironment();

  // If already destined for Tier 3 or 2 from static environment, no need for frame probe
  const preliminary = evaluateCapabilities(env);
  if (preliminary > 1 || skipFrameProbe) {
    applyMotionTier(preliminary);
    try {
      sessionStorage.setItem(STORAGE_KEY_SESSION_TIER, String(preliminary));
    } catch (_) {}
    return preliminary;
  }

  // Run 400ms frame probe to verify device can sustain 40+ FPS
  const medianDelta = await runFrameProbe(400);
  env.medianFrameDelta = medianDelta;

  const finalTier = evaluateCapabilities(env);
  applyMotionTier(finalTier);
  try {
    sessionStorage.setItem(STORAGE_KEY_SESSION_TIER, String(finalTier));
  } catch (_) {}
  return finalTier;
}

/**
 * Updates DOM attribute and dispatches change event.
 *
 * @param {number} tier
 */
export function applyMotionTier(tier) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.motionTier = String(tier);
  const event = new CustomEvent("motiontierchange", {
    detail: { tier },
    bubbles: true,
  });
  window.dispatchEvent(event);
}

/**
 * Programmatically sets or clears the manual "Reduce motion" preference.
 *
 * @param {"reduced"|"auto"} pref
 */
export function setManualMotionPreference(pref) {
  try {
    if (pref === "reduced") {
      localStorage.setItem(STORAGE_KEY_USER_PREF, "reduced");
    } else {
      localStorage.removeItem(STORAGE_KEY_USER_PREF);
    }
    // Clear session cache so it re-evaluates
    sessionStorage.removeItem(STORAGE_KEY_SESSION_TIER);
  } catch (_) {}

  // Re-run evaluation
  initMotionTier(true);
}

/**
 * Initializes the visible "Reduce motion" button in the footer.
 * Sets persistent preference in localStorage, updates document dataset, and toggles button label.
 */
export function initMotionToggleButton() {
  if (typeof document === "undefined") return;
  const btn = document.getElementById("toggle-reduce-motion");
  if (!btn) return;

  function updateButtonState() {
    let isStoredReduced = false;
    try {
      isStoredReduced = localStorage.getItem(STORAGE_KEY_USER_PREF) === "reduced";
    } catch (_) {}
    const osReduced =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const isReduced = isStoredReduced || osReduced;

    btn.setAttribute("aria-pressed", isReduced ? "true" : "false");
    const label = btn.querySelector(".motion-toggle-label");
    if (label) {
      label.textContent = isReduced ? "Reduce motion: On" : "Reduce motion: Off";
    }
  }

  // Update on initial render
  updateButtonState();

  btn.addEventListener("click", () => {
    const isCurrentlyReduced = btn.getAttribute("aria-pressed") === "true";
    if (isCurrentlyReduced) {
      setManualMotionPreference("auto");
    } else {
      setManualMotionPreference("reduced");
    }
    updateButtonState();
  });
}

