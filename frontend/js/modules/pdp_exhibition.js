/**
 * ELECTROCART PDP Exhibition Frame & Commerce Interaction Module (WP6).
 * Features:
 * - Exhibition plate entrance choreography (Tier 1-2).
 * - Secondary thumbnail switching (available on all tiers).
 * - Spec table hairline draws across on entrance.
 * - Native <dialog> Lightbox with pan/zoom (Tier 1-3).
 * - Sticky sub-nav with scrollspy & smooth section scrolling.
 * - Flying thumbnail ghost to cart bag icon with mini-bag confirmation dialog.
 */

export function initPdpExhibition() {
  if (typeof window === "undefined" || typeof document === "undefined") return;

  const plate = document.querySelector(".product-frame-mat");
  if (!plate) return;

  const tier = document.documentElement.dataset.motionTier || "1";
  const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Secondary thumbnail switching (available on all tiers)
  setupThumbnailStrip();

  // WP6: Lightbox controller
  setupLightbox();

  // WP6: Sticky Sub-nav Scrollspy
  setupStickySubnav();

  // WP6: Fly-to-bag & Mini-bag confirmation
  setupFlyToBag();

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

function setupLightbox() {
  const openBtn = document.getElementById("open-lightbox-btn");
  const dialog = document.getElementById("pdp-lightbox-dialog");
  const closeBtn = document.getElementById("close-lightbox-btn");
  const stage = document.getElementById("lightbox-stage");

  if (!openBtn || !dialog) return;

  openBtn.addEventListener("click", () => {
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "true");
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      if (typeof dialog.close === "function") {
        dialog.close();
      } else {
        dialog.removeAttribute("open");
      }
    });
  }

  // Close when clicking outside dialog content
  dialog.addEventListener("click", (e) => {
    const rect = dialog.getBoundingClientRect();
    const isInDialog = (
      rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX && e.clientX <= rect.left + rect.width
    );
    if (!isInDialog) {
      if (typeof dialog.close === "function") {
        dialog.close();
      } else {
        dialog.removeAttribute("open");
      }
    }
  });

  // Toggle zoom on image stage
  if (stage) {
    stage.addEventListener("click", () => {
      stage.classList.toggle("is-zoomed");
    });
  }
}

function setupStickySubnav() {
  const subnav = document.getElementById("pdp-sticky-subnav");
  if (!subnav) return;

  const tabs = subnav.querySelectorAll(".pdp-subnav-tab");
  if (!tabs.length) return;

  // Smooth scroll with offset for sticky header + subnav
  tabs.forEach((tab) => {
    tab.addEventListener("click", (e) => {
      const targetId = tab.getAttribute("href");
      if (targetId && targetId.startsWith("#")) {
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          e.preventDefault();
          const offset = 130;
          const bodyRect = document.body.getBoundingClientRect().top;
          const elementRect = targetEl.getBoundingClientRect().top;
          const elementPosition = elementRect - bodyRect;
          const offsetPosition = elementPosition - offset;

          window.scrollTo({
            top: offsetPosition,
            behavior: "smooth"
          });
        }
      }
    });
  });

  // Scrollspy observer
  const sectionIds = ["section-overview", "section-specs", "section-box", "section-compare"];
  const sections = sectionIds.map((id) => document.getElementById(id)).filter(Boolean);

  if (!sections.length || typeof IntersectionObserver === "undefined") return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          tabs.forEach((tab) => {
            const href = tab.getAttribute("href");
            if (href === `#${id}`) {
              tab.classList.add("is-active");
            } else {
              tab.classList.remove("is-active");
            }
          });
        }
      });
    },
    {
      rootMargin: "-20% 0px -70% 0px",
      threshold: 0
    }
  );

  sections.forEach((sec) => observer.observe(sec));
}

function setupFlyToBag() {
  const miniBagDialog = document.getElementById("mini-bag-dialog");
  const closeMiniBagBtn = document.getElementById("close-mini-bag-btn");

  if (closeMiniBagBtn && miniBagDialog) {
    closeMiniBagBtn.addEventListener("click", () => {
      if (typeof miniBagDialog.close === "function") {
        miniBagDialog.close();
      } else {
        miniBagDialog.removeAttribute("open");
      }
    });

    miniBagDialog.addEventListener("click", (e) => {
      const rect = miniBagDialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX && e.clientX <= rect.left + rect.width
      );
      if (!isInDialog) {
        if (typeof miniBagDialog.close === "function") {
          miniBagDialog.close();
        } else {
          miniBagDialog.removeAttribute("open");
        }
      }
    });
  }

  // Intercept cart add forms on the PDP
  const addForms = document.querySelectorAll('form[action*="/cart/add/"]');
  if (!addForms.length) return;

  addForms.forEach((form) => {
    form.addEventListener("submit", () => {
      const tier = document.documentElement.dataset.motionTier || "1";
      const isReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      const mainImg = document.querySelector(".product-frame-img");
      const bagTarget = document.querySelector(".header-bag-link") || document.querySelector("a[href*='/cart/']");

      if (miniBagDialog) {
        setTimeout(() => {
          if (typeof miniBagDialog.showModal === "function") {
            try {
              if (!miniBagDialog.open) miniBagDialog.showModal();
            } catch (_) {}
          } else {
            miniBagDialog.setAttribute("open", "true");
          }
        }, tier === "3" || isReduced ? 100 : 350);
      }

      if (tier === "3" || isReduced || !mainImg || !bagTarget) {
        return;
      }

      // Create 48x48 ghost thumbnail at button coordinates
      const btn = form.querySelector('button[type="submit"]');
      const originRect = btn ? btn.getBoundingClientRect() : mainImg.getBoundingClientRect();
      const bagCountTarget = document.querySelector("#header-bag-count") || document.querySelector(".header-bag-link") || document.querySelector("a[href*='/cart/']");
      const bagRect = bagCountTarget.getBoundingClientRect();

      const ghost = document.createElement("div");
      ghost.className = "fly-to-bag-ghost";
      ghost.style.width = "48px";
      ghost.style.height = "48px";
      ghost.style.left = `${originRect.left + (originRect.width - 48) / 2}px`;
      ghost.style.top = `${originRect.top + (originRect.height - 48) / 2}px`;
      ghost.style.transition = "transform 500ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 500ms ease";

      const ghostImg = document.createElement("img");
      ghostImg.src = mainImg.src;
      ghostImg.alt = "";
      ghost.appendChild(ghostImg);
      document.body.appendChild(ghost);

      // Animate towards #header-bag-count over 0.5s
      requestAnimationFrame(() => {
        const deltaX = (bagRect.left + bagRect.width / 2) - (originRect.left + originRect.width / 2);
        const deltaY = (bagRect.top + bagRect.height / 2) - (originRect.top + originRect.height / 2);

        ghost.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(0.2)`;
        ghost.style.opacity = "0";

        setTimeout(() => {
          if (ghost.parentNode) ghost.parentNode.removeChild(ghost);
          if (bagCountTarget) {
            bagCountTarget.classList.add("bag-pulse");
            setTimeout(() => {
              bagCountTarget.classList.remove("bag-pulse");
            }, 250);
          }
        }, 500);
      });
    });
  });
}
