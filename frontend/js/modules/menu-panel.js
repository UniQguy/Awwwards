/**
 * Progressive disclosure menu panel handler and dynamic preview coordinator.
 * Features:
 * 1. Closes on Escape and clicks outside, restoring focus to summary element.
 * 2. Syncs aria-expanded on details toggle.
 * 3. Dynamic category preview pane (cutout image, starting price, brand chips, budget shortcut)
 *    on category item hover/focus with smooth opacity transition.
 * 4. Keyboard ArrowUp / ArrowDown navigation through category items.
 */
export function initMenuPanel() {
  const details = document.querySelector(".shop-menu-details");
  if (!details) return;

  const summary = details.querySelector(".shop-menu-summary");
  const catItems = details.querySelectorAll(".mega-menu-cat-item");
  const previewImg = details.querySelector("#mega-preview-img");
  const previewFallback = details.querySelector("#mega-preview-fallback");
  const previewCatLabel = details.querySelector("#mega-preview-cat-label");
  const previewPriceVal = details.querySelector("#mega-preview-price-val");
  const previewBrandChips = details.querySelector("#mega-preview-brand-chips");
  const previewBudgetLink = details.querySelector("#mega-preview-budget-link");
  const previewViewLink = details.querySelector("#mega-preview-view-link");

  // Sync aria-expanded
  const updateAria = () => {
    if (summary) {
      summary.setAttribute("aria-expanded", details.open ? "true" : "false");
    }
  };
  details.addEventListener("toggle", updateAria);
  updateAria();

  // Outside click closes panel
  document.addEventListener("click", (e) => {
    if (details.open && !details.contains(e.target)) {
      details.removeAttribute("open");
      updateAria();
    }
  });

  // Escape key closes panel and restores focus
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && details.open) {
      details.removeAttribute("open");
      updateAria();
      if (summary) summary.focus();
    }
  });

  // Keyboard ArrowUp / ArrowDown navigation inside category list
  const catList = details.querySelector(".mega-menu-cat-list");
  if (catList && catItems.length > 0) {
    catList.addEventListener("keydown", (e) => {
      const activeElement = document.activeElement;
      const index = Array.from(catItems).indexOf(activeElement);
      if (index === -1) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = catItems[(index + 1) % catItems.length];
        next.focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = catItems[(index - 1 + catItems.length) % catItems.length];
        prev.focus();
      } else if (e.key === "Home") {
        e.preventDefault();
        catItems[0].focus();
      } else if (e.key === "End") {
        e.preventDefault();
        catItems[catItems.length - 1].focus();
      }
    });
  }

  // Category hover/focus preview synchronization
  function activateCategory(item) {
    if (!item) return;

    catItems.forEach((el) => el.classList.remove("is-active"));
    item.classList.add("is-active");

    const catSlug = item.dataset.catSlug || "";
    const catName = item.dataset.catName || "";
    const catPrice = item.dataset.catPrice || "";
    const catCutout = item.dataset.catCutout || "";
    const catBrandsRaw = item.dataset.catBrands || "";
    const catBudgetLabel = item.dataset.catBudgetLabel || "";
    const catBudgetUrl = item.dataset.catBudgetUrl || "";

    if (previewCatLabel) {
      previewCatLabel.textContent = catName;
    }

    if (previewPriceVal) {
      previewPriceVal.textContent = catPrice;
    }

    if (previewImg) {
      if (catCutout) {
        previewImg.style.opacity = "0.3";
        previewImg.src = catCutout;
        previewImg.style.display = "";
        if (previewFallback) previewFallback.style.display = "none";
        setTimeout(() => {
          previewImg.style.opacity = "1";
        }, 50);
      } else {
        previewImg.style.display = "none";
        if (previewFallback) {
          previewFallback.style.display = "flex";
          const initSpan = previewFallback.querySelector(".image-fallback-initial");
          if (initSpan) initSpan.textContent = catName.charAt(0);
        }
      }
    }

    if (previewBrandChips) {
      previewBrandChips.innerHTML = "";
      if (catBrandsRaw) {
        const brands = catBrandsRaw.split(",").map((s) => s.trim()).filter(Boolean);
        brands.forEach((brand) => {
          const chip = document.createElement("a");
          chip.className = "mega-brand-chip";
          chip.href = `/c/${catSlug}/?brand=${encodeURIComponent(brand)}`;
          chip.textContent = brand;
          previewBrandChips.appendChild(chip);
        });
      }
    }

    if (previewBudgetLink) {
      previewBudgetLink.textContent = `${catBudgetLabel} \u2192`;
      previewBudgetLink.href = catBudgetUrl;
    }

    if (previewViewLink) {
      previewViewLink.textContent = `Explore ${catName} \u2192`;
      previewViewLink.href = `/c/${catSlug}/`;
    }
  }

  catItems.forEach((item) => {
    item.addEventListener("mouseenter", () => activateCategory(item));
    item.addEventListener("focus", () => activateCategory(item));
  });
}
