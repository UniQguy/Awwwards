/**
 * ELECTROCART Price Histogram & Dual-Thumb Slider Module (WP6).
 * Progressive enhancement over server-rendered min/max price inputs and bracket selector.
 *
 * Rules:
 * - Reads bracket data embedded via json_script (#price-brackets-data).
 * - Inline SVG histogram with log-scaled bar heights.
 * - Dual-thumb ARIA slider pattern (role="slider", aria-valuenow, aria-valuemin, aria-valuemax, aria-valuetext).
 * - Stepped log-like scale mapping with Indian Rupee formatting.
 * - Keyboard navigation (Arrows, PageUp/Down, Home, End).
 * - Dragging updates inputs and requests live result-count hint from /c/<slug>/count/.
 * - Debounces requests (250ms); aborts stale ones with AbortController.
 * - 44px minimum touch targets.
 */

export const STEP_POINTS = [
  0,
  250,
  500,
  750,
  1000,
  1500,
  2000,
  2500,
  3500,
  5000,
  7500,
  10000,
  15000,
  20000,
  30000,
  40000,
  60000,
  80000,
  100000,
  150000,
];

/**
 * Formats a numeric value into Indian Rupee representation with Indian numbering grouping.
 *
 * @param {number} val
 * @returns {string}
 */
export function formatINR(val) {
  if (val === null || val === undefined || isNaN(val)) return "₹0";
  const num = Math.round(Number(val));
  // Indian numbering grouping format (e.g. 1,00,000)
  const str = String(num);
  let result = "";
  if (str.length <= 3) {
    result = str;
  } else {
    const lastThree = str.substring(str.length - 3);
    const rest = str.substring(0, str.length - 3);
    result = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",") + "," + lastThree;
  }
  return `₹${result}`;
}

/**
 * Finds the index in STEP_POINTS closest to a given price value.
 *
 * @param {number} price
 * @param {number[]} [steps=STEP_POINTS]
 * @returns {number}
 */
export function findNearestStepIndex(price, steps = STEP_POINTS) {
  if (!steps || steps.length === 0) return 0;
  let closestIdx = 0;
  let minDiff = Infinity;
  for (let i = 0; i < steps.length; i++) {
    const diff = Math.abs(steps[i] - price);
    if (diff < minDiff) {
      minDiff = diff;
      closestIdx = i;
    }
  }
  return closestIdx;
}

/**
 * Maps a step index to percentage [0, 100].
 *
 * @param {number} index
 * @param {number} totalSteps
 * @returns {number}
 */
export function indexToPercent(index, totalSteps = STEP_POINTS.length) {
  if (totalSteps <= 1) return 0;
  const clamped = Math.max(0, Math.min(totalSteps - 1, index));
  return parseFloat(((clamped / (totalSteps - 1)) * 100).toFixed(2));
}

/**
 * Maps a percentage [0, 100] to the nearest step index.
 *
 * @param {number} pct
 * @param {number} totalSteps
 * @returns {number}
 */
export function percentToIndex(pct, totalSteps = STEP_POINTS.length) {
  if (totalSteps <= 1) return 0;
  const fraction = Math.max(0, Math.min(100, pct)) / 100;
  return Math.round(fraction * (totalSteps - 1));
}

let activeAbortController = null;
let debounceTimer = null;

/**
 * Initializes the dual-thumb range slider progressive enhancement on category pages.
 */
export function initPriceHistogram() {
  if (typeof document === "undefined") return;

  const mount = document.getElementById("price-slider-mount");
  const dataScript = document.getElementById("price-brackets-data");
  const minInput = document.getElementById("filter-min-price");
  const maxInput = document.getElementById("filter-max-price");

  if (!mount || !dataScript || !minInput || !maxInput) return;

  let brackets = [];
  try {
    brackets = JSON.parse(dataScript.textContent || "[]");
  } catch (_) {
    return;
  }

  const categorySlug = mount.dataset.category || "";

  // Initial values from form inputs or defaults
  const initialMinPrice = minInput.value ? Number(minInput.value) : STEP_POINTS[0];
  const initialMaxPrice = maxInput.value ? Number(maxInput.value) : STEP_POINTS[STEP_POINTS.length - 1];

  let minStepIdx = findNearestStepIndex(initialMinPrice);
  let maxStepIdx = findNearestStepIndex(initialMaxPrice);
  if (minStepIdx > maxStepIdx) {
    minStepIdx = maxStepIdx;
  }

  // Render widget structure into mount
  mount.innerHTML = `
    <div class="price-histogram-container" aria-hidden="true">
      <svg class="price-histogram-svg" viewBox="0 0 100 40" preserveAspectRatio="none">
        ${renderBars(brackets, STEP_POINTS[minStepIdx], STEP_POINTS[maxStepIdx])}
      </svg>
    </div>
    <div class="range-slider-wrapper">
      <div class="range-slider-track"></div>
      <div class="range-slider-progress" id="slider-progress"></div>
      <div
        class="range-slider-thumb"
        id="thumb-min"
        role="slider"
        tabindex="0"
        aria-label="Minimum price"
        aria-valuemin="${STEP_POINTS[0]}"
        aria-valuemax="${STEP_POINTS[maxStepIdx]}"
        aria-valuenow="${STEP_POINTS[minStepIdx]}"
        aria-valuetext="${formatINR(STEP_POINTS[minStepIdx])}"
      ></div>
      <div
        class="range-slider-thumb"
        id="thumb-max"
        role="slider"
        tabindex="0"
        aria-label="Maximum price"
        aria-valuemin="${STEP_POINTS[minStepIdx]}"
        aria-valuemax="${STEP_POINTS[STEP_POINTS.length - 1]}"
        aria-valuenow="${STEP_POINTS[maxStepIdx]}"
        aria-valuetext="${formatINR(STEP_POINTS[maxStepIdx])}"
      ></div>
    </div>
    <div class="price-slider-footer">
      <span id="price-display-range">${formatINR(STEP_POINTS[minStepIdx])} &ndash; ${formatINR(STEP_POINTS[maxStepIdx])}</span>
      <span class="price-count-hint" id="price-count-hint"></span>
    </div>
  `;

  const thumbMin = mount.querySelector("#thumb-min");
  const thumbMax = mount.querySelector("#thumb-max");
  const progressBar = mount.querySelector("#slider-progress");
  const displayRange = mount.querySelector("#price-display-range");
  const countHint = mount.querySelector("#price-count-hint");
  const svg = mount.querySelector(".price-histogram-svg");
  const wrapper = mount.querySelector(".range-slider-wrapper");

  function updateVisuals() {
    const minPct = indexToPercent(minStepIdx);
    const maxPct = indexToPercent(maxStepIdx);
    const minVal = STEP_POINTS[minStepIdx];
    const maxVal = STEP_POINTS[maxStepIdx];

    thumbMin.style.left = `${minPct}%`;
    thumbMax.style.left = `${maxPct}%`;

    progressBar.style.left = `${minPct}%`;
    progressBar.style.width = `${maxPct - minPct}%`;

    thumbMin.setAttribute("aria-valuenow", String(minVal));
    thumbMin.setAttribute("aria-valuemax", String(maxVal));
    thumbMin.setAttribute("aria-valuetext", formatINR(minVal));

    thumbMax.setAttribute("aria-valuenow", String(maxVal));
    thumbMax.setAttribute("aria-valuemin", String(minVal));
    thumbMax.setAttribute("aria-valuetext", formatINR(maxVal));

    minInput.value = minStepIdx > 0 ? String(minVal) : "";
    maxInput.value = maxStepIdx < STEP_POINTS.length - 1 ? String(maxVal) : "";

    displayRange.innerHTML = `${formatINR(minVal)} &ndash; ${formatINR(maxVal)}`;

    // Update SVG bar highlighting
    if (svg) {
      svg.innerHTML = renderBars(brackets, minVal, maxVal);
    }
  }

  function debouncedFetchCount() {
    if (debounceTimer) clearTimeout(debounceTimer);
    if (activeAbortController) {
      activeAbortController.abort();
    }

    countHint.textContent = "Checking...";

    debounceTimer = setTimeout(async () => {
      activeAbortController = new AbortController();
      try {
        const brandSelect = document.getElementById("filter-brand");
        const collapsedCheckbox = document.getElementById("filter-collapsed");

        const brand = brandSelect ? brandSelect.value : "";
        const collapsed = collapsedCheckbox && collapsedCheckbox.checked ? "1" : "0";

        const params = new URLSearchParams();
        if (minInput.value) params.set("min_price", minInput.value);
        if (maxInput.value) params.set("max_price", maxInput.value);
        if (brand) params.set("brand", brand);
        if (collapsed === "1") params.set("collapsed", "1");

        const res = await fetch(`/c/${categorySlug}/count/?${params.toString()}`, {
          signal: activeAbortController.signal,
          headers: { Accept: "application/json" },
        });

        if (res.ok) {
          const data = await res.json();
          countHint.textContent = `${data.count} product${data.count === 1 ? "" : "s"}`;
        } else {
          countHint.textContent = "";
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          countHint.textContent = "";
        }
      }
    }, 250);
  }

  function handleDrag(thumbType, clientX) {
    const rect = wrapper.getBoundingClientRect();
    if (rect.width <= 0) return;
    const pct = ((clientX - rect.left) / rect.width) * 100;
    const newIdx = percentToIndex(pct);

    if (thumbType === "min") {
      minStepIdx = Math.min(newIdx, maxStepIdx);
    } else {
      maxStepIdx = Math.max(newIdx, minStepIdx);
    }

    updateVisuals();
    debouncedFetchCount();
  }

  // Pointer drag interactions
  [
    { el: thumbMin, type: "min" },
    { el: thumbMax, type: "max" },
  ].forEach(({ el, type }) => {
    el.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      el.setPointerCapture(e.pointerId);

      function onMove(moveEvent) {
        handleDrag(type, moveEvent.clientX);
      }

      function onUp(upEvent) {
        try {
          el.releasePointerCapture(upEvent.pointerId);
        } catch (_) {}
        el.removeEventListener("pointermove", onMove);
        el.removeEventListener("pointerup", onUp);
        el.removeEventListener("pointercancel", onUp);
      }

      el.addEventListener("pointermove", onMove);
      el.addEventListener("pointerup", onUp);
      el.addEventListener("pointercancel", onUp);
    });

    // Keyboard accessibility
    el.addEventListener("keydown", (e) => {
      let changed = false;
      let cur = type === "min" ? minStepIdx : maxStepIdx;

      switch (e.key) {
        case "ArrowLeft":
        case "ArrowDown":
          cur = Math.max(0, cur - 1);
          changed = true;
          break;
        case "ArrowRight":
        case "ArrowUp":
          cur = Math.min(STEP_POINTS.length - 1, cur + 1);
          changed = true;
          break;
        case "PageDown":
          cur = Math.max(0, cur - 3);
          changed = true;
          break;
        case "PageUp":
          cur = Math.min(STEP_POINTS.length - 1, cur + 3);
          changed = true;
          break;
        case "Home":
          cur = type === "min" ? 0 : minStepIdx;
          changed = true;
          break;
        case "End":
          cur = type === "min" ? maxStepIdx : STEP_POINTS.length - 1;
          changed = true;
          break;
      }

      if (changed) {
        e.preventDefault();
        if (type === "min") {
          minStepIdx = Math.min(cur, maxStepIdx);
        } else {
          maxStepIdx = Math.max(cur, minStepIdx);
        }
        updateVisuals();
        debouncedFetchCount();
      }
    });
  });

  // Initial setup
  updateVisuals();
}

/**
 * Generates SVG rect elements for bracket bars.
 *
 * @param {Array} brackets
 * @param {number} minVal
 * @param {number} maxVal
 * @returns {string}
 */
function renderBars(brackets, minVal, maxVal) {
  if (!Array.isArray(brackets) || brackets.length === 0) return "";
  const total = brackets.length;
  const barWidth = 100 / total - 2;

  return brackets
    .map((bar, i) => {
      const x = i * (100 / total) + 1;
      const rawPct = Number(bar.height_pct ?? bar.height_percent ?? 0);
      const safePct = isNaN(rawPct) ? 0 : rawPct;
      const height = Math.max(4, Math.min(38, (safePct / 100) * 38));
      const y = 40 - height;
      const barMin = Number(bar.min_price || 0);
      const barMax = bar.max_price !== null && bar.max_price !== undefined ? Number(bar.max_price) : Infinity;

      const inRange = barMin <= maxVal && barMax >= minVal;
      const cls = inRange ? "price-histogram-bar is-in-range" : "price-histogram-bar is-out-of-range";

      return `<rect class="${cls}" x="${x.toFixed(1)}%" y="${y.toFixed(1)}" width="${barWidth.toFixed(1)}%" height="${height.toFixed(1)}" rx="1"></rect>`;
    })
    .join("");
}
