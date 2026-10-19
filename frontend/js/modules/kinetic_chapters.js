/**
 * ELECTROCART Kinetic Monograph Exhibition Modules (Phase R8, Task 5)
 * Handles:
 * - Flagship Anatomy scrubbed layer stepping
 * - Vault coupon click-to-copy
 * - Spec duel bar animations
 * - Desk setup bundle dynamic price calculation
 * - Hero WebGL scene mounting
 */

import { initHeroWebGL } from "./hero_webgl.js";

export function initKineticChapters() {
  initHeroWebGLMount();
  initFlagshipAnatomy();
  initVaultCoupons();
  initSpecDuelAnimation();
  initDeskBundleBuilder();
}

/**
 * Mounts Three.js WebGL scene on Chapter 01 hero plate if supported.
 */
export function initHeroWebGLMount() {
  const mountContainer = document.getElementById("hero-webgl-canvas-container");
  const plateSlot = document.getElementById("hero-plate-slot");
  if (!mountContainer || !plateSlot) return;

  const imageUrl = plateSlot.dataset.heroImg;
  if (!imageUrl) return;

  const tier = parseInt(document.documentElement.dataset.motionTier || "1", 10);
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (tier === 3 || isReduced) return;

  try {
    initHeroWebGL(mountContainer, imageUrl);
  } catch (err) {
    console.warn("Could not mount hero WebGL:", err);
  }
}

/**
 * Chapter 02: Interactive Hardware Anatomy Layer Controller.
 */
export function initFlagshipAnatomy() {
  const chapter = document.getElementById("flagship-anatomy-chapter");
  if (!chapter) return;

  const tabs = chapter.querySelectorAll(".anatomy-layer-tab");
  const stageImg = chapter.querySelector(".anatomy-stage-img");
  const layerBadge = chapter.querySelector(".anatomy-layer-badge");
  const layerDetails = chapter.querySelectorAll(".anatomy-layer-detail");

  function switchLayer(idx) {
    tabs.forEach((tab, i) => {
      if (i === idx) {
        tab.classList.add("is-active");
        tab.setAttribute("aria-selected", "true");
      } else {
        tab.classList.remove("is-active");
        tab.setAttribute("aria-selected", "false");
      }
    });

    if (layerBadge) {
      layerBadge.textContent = `LAYER 0${idx + 1} OF 04`;
    }

    if (stageImg) {
      if (idx === 0) {
        stageImg.style.transform = "scale(1.05) rotate(0deg)";
        stageImg.style.filter = "contrast(1.1) brightness(1.02)";
      } else if (idx === 1) {
        stageImg.style.transform = "scale(0.95) rotate(-2deg)";
        stageImg.style.filter = "contrast(1.2) hue-rotate(15deg)";
      } else if (idx === 2) {
        stageImg.style.transform = "scale(1) rotate(1.5deg)";
        stageImg.style.filter = "grayscale(0.3) brightness(1.05)";
      } else {
        stageImg.style.transform = "scale(1.08) rotate(0deg)";
        stageImg.style.filter = "none";
      }
    }

    layerDetails.forEach((detail, i) => {
      detail.style.display = i === idx ? "block" : "none";
    });
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => switchLayer(i));
  });

  // GSAP ScrollTrigger Scrub for desktop if available
  const gsapObj = window.gsap || (typeof gsap !== "undefined" ? gsap : null);
  const stObj = window.ScrollTrigger || (typeof ScrollTrigger !== "undefined" ? ScrollTrigger : null);
  const tier = parseInt(document.documentElement.dataset.motionTier || "1", 10);
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (gsapObj && stObj && tier === 1 && !isReduced && window.innerWidth >= 1024) {
    try {
      gsapObj.registerPlugin(stObj);
      stObj.create({
        trigger: chapter,
        start: "top top+=100",
        end: "+=120%",
        pin: false,
        onUpdate: (self) => {
          const progress = self.progress;
          const targetIndex = Math.min(3, Math.floor(progress * 4));
          switchLayer(targetIndex);
        },
      });
    } catch (_) {}
  }
}

/**
 * Chapter 03: Click to Copy Coupon Codes.
 */
export function initVaultCoupons() {
  const couponPills = document.querySelectorAll(".coupon-code-pill");
  couponPills.forEach((pill) => {
    pill.addEventListener("click", async () => {
      const code = pill.dataset.code || pill.textContent.trim().split(" ")[0];
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(code);
        }
        const originalText = pill.innerHTML;
        pill.innerHTML = `<span>COPIED</span> <span>&#10003;</span>`;
        setTimeout(() => {
          pill.innerHTML = originalText;
        }, 2000);
      } catch (err) {
        console.warn("Could not copy coupon code:", err);
      }
    });
  });
}

/**
 * Chapter 04: Head-to-Head Spec Duel Animated Bars.
 */
export function initSpecDuelAnimation() {
  const duelSection = document.getElementById("spec-duel-chapter");
  if (!duelSection) return;

  const fills = duelSection.querySelectorAll(".duel-bar-left-fill, .duel-bar-right-fill");
  if (!fills.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          fills.forEach((fill) => {
            const width = fill.dataset.width || "50%";
            fill.style.width = width;
            fill.style.transition = "width 0.8s cubic-bezier(0.16, 1, 0.3, 1)";
          });
          observer.disconnect();
        }
      });
    },
    { threshold: 0.2 }
  );

  observer.observe(duelSection);
}

/**
 * Chapter 07: Curate Your Desk Setup Bundle Builder.
 */
export function initDeskBundleBuilder() {
  const bundleSection = document.getElementById("desk-bundle-chapter");
  if (!bundleSection) return;

  const columns = bundleSection.querySelectorAll(".bundle-column");
  const priceDisplay = bundleSection.querySelector(".bundle-summary-price");
  const countDisplay = bundleSection.querySelector(".setup-summary-count");
  const savingsDisplay = bundleSection.querySelector(".setup-summary-savings");
  const hiddenInput = bundleSection.querySelector("#bundle-product-ids");
  const submitBtn = bundleSection.querySelector("#bundle-submit-btn");
  if (!columns.length || !priceDisplay || !hiddenInput) return;

  function updateBundleTotal() {
    let total = 0;
    let mrpTotal = 0;
    const selectedIds = [];

    columns.forEach((col) => {
      const activeCard = col.querySelector(".bundle-picker-card.is-selected");
      if (activeCard) {
        const price = parseFloat(activeCard.dataset.price || "0");
        const mrp = parseFloat(activeCard.dataset.mrp || activeCard.dataset.price || "0");
        const pid = activeCard.dataset.id;
        total += price;
        mrpTotal += Math.max(mrp, price);
        if (pid) selectedIds.push(pid);
      }
    });

    const savings = Math.max(0, mrpTotal - total);
    priceDisplay.textContent = `₹${Math.round(total).toLocaleString("en-IN")}`;
    if (countDisplay) {
      countDisplay.textContent = `${selectedIds.length} Component${selectedIds.length === 1 ? "" : "s"}`;
    }
    if (savingsDisplay) {
      savingsDisplay.textContent = `Save ₹${Math.round(savings).toLocaleString("en-IN")}`;
    }
    hiddenInput.value = selectedIds.join(",");

    if (submitBtn) {
      if (selectedIds.length === 0) {
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.5";
        submitBtn.style.pointerEvents = "none";
      } else {
        submitBtn.disabled = false;
        submitBtn.style.opacity = "1";
        submitBtn.style.pointerEvents = "auto";
      }
    }
  }

  columns.forEach((col) => {
    const cards = col.querySelectorAll(".bundle-picker-card");
    cards.forEach((card) => {
      const handleToggle = () => {
        const wasSelected = card.classList.contains("is-selected");

        cards.forEach((c) => {
          c.classList.remove("is-selected");
          c.setAttribute("aria-pressed", "false");
          const pill = c.querySelector(".bundle-card-status-pill");
          if (pill) {
            pill.textContent = "Select";
            pill.className = "bundle-card-status-pill badge badge-neutral text-3xs font-mono";
          }
        });

        if (!wasSelected) {
          card.classList.add("is-selected");
          card.setAttribute("aria-pressed", "true");
          const pill = card.querySelector(".bundle-card-status-pill");
          if (pill) {
            pill.textContent = "Selected ✓";
            pill.className = "bundle-card-status-pill badge badge-accent text-3xs font-mono";
          }
        }

        updateBundleTotal();
      };

      card.addEventListener("click", handleToggle);
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          handleToggle();
        }
      });
    });
  });

  updateBundleTotal();
}
