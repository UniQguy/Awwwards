import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { initMenuPanel } from "../../frontend/js/modules/menu-panel.js";

describe("menu-panel.js", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <details class="shop-menu-details" id="shop-menu-details">
        <summary class="shop-menu-summary" aria-haspopup="true">
          <span>Shop</span>
        </summary>
        <div class="shop-dropdown-panel mega-menu-panel" id="mega-menu-panel" role="region">
          <div class="mega-menu-grid">
            <div class="mega-menu-list-col">
              <div class="mega-menu-cat-list" role="list">
                <a
                  href="/c/audio/"
                  class="mega-menu-cat-item is-active"
                  role="listitem"
                  data-cat-slug="audio"
                  data-cat-name="Audio & Sound"
                  data-cat-count="120"
                  data-cat-price="₹1,299"
                  data-cat-cutout="https://example.com/audio.png"
                  data-cat-brands="Sony, Bose, JBL"
                  data-cat-budget-label="Under ₹1,999"
                  data-cat-budget-url="/c/audio/?max_price=1999"
                >
                  <span class="shop-cat-name">Audio & Sound</span>
                  <span class="shop-cat-count">120</span>
                </a>
                <a
                  href="/c/keyboards/"
                  class="mega-menu-cat-item"
                  role="listitem"
                  data-cat-slug="keyboards"
                  data-cat-name="Keyboards & Mice"
                  data-cat-count="45"
                  data-cat-price="₹799"
                  data-cat-cutout=""
                  data-cat-brands="Logitech, Keychron"
                  data-cat-budget-label="Under ₹999"
                  data-cat-budget-url="/c/keyboards/?max_price=999"
                >
                  <span class="shop-cat-name">Keyboards & Mice</span>
                  <span class="shop-cat-count">45</span>
                </a>
              </div>
            </div>
            <div class="mega-menu-preview-col" id="mega-menu-preview-pane">
              <div class="mega-preview-card" id="mega-preview-card">
                <div class="mega-preview-plate">
                  <img src="https://example.com/audio.png" alt="" class="mega-preview-img" id="mega-preview-img">
                  <div class="image-fallback-plate" id="mega-preview-fallback" style="display: none;">
                    <span class="image-fallback-initial">A</span>
                  </div>
                </div>
                <div class="mega-preview-meta">
                  <span class="mega-preview-cat-label" id="mega-preview-cat-label">Audio & Sound</span>
                  <p class="mega-preview-price-line" id="mega-preview-price-line">Priced from <strong id="mega-preview-price-val">₹1,299</strong></p>
                  <div class="mega-preview-brand-chips" id="mega-preview-brand-chips"></div>
                  <a href="/c/audio/?max_price=1999" class="mega-budget-link" id="mega-preview-budget-link">Under ₹1,999 &rarr;</a>
                  <a href="/c/audio/" class="btn btn-sm btn-primary" id="mega-preview-view-link">Explore Audio & Sound &rarr;</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </details>
      <div id="outside-elem">Outside</div>
    `;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("syncs aria-expanded on details toggle", () => {
    initMenuPanel();
    const details = document.getElementById("shop-menu-details");
    const summary = details.querySelector(".shop-menu-summary");

    expect(summary.getAttribute("aria-expanded")).toBe("false");

    details.open = true;
    details.dispatchEvent(new Event("toggle"));
    expect(summary.getAttribute("aria-expanded")).toBe("true");

    details.open = false;
    details.dispatchEvent(new Event("toggle"));
    expect(summary.getAttribute("aria-expanded")).toBe("false");
  });

  it("closes details when clicking outside", () => {
    initMenuPanel();
    const details = document.getElementById("shop-menu-details");
    details.open = true;

    const outside = document.getElementById("outside-elem");
    outside.dispatchEvent(new MouseEvent("click", { bubbles: true }));

    expect(details.open).toBe(false);
  });

  it("closes details and restores focus on Escape key", () => {
    initMenuPanel();
    const details = document.getElementById("shop-menu-details");
    const summary = details.querySelector(".shop-menu-summary");
    const focusSpy = vi.spyOn(summary, "focus");

    details.open = true;
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));

    expect(details.open).toBe(false);
    expect(focusSpy).toHaveBeenCalled();
  });

  it("updates preview pane when hovering or focusing another category", () => {
    initMenuPanel();
    const items = document.querySelectorAll(".mega-menu-cat-item");
    const keyboardItem = items[1];

    keyboardItem.dispatchEvent(new Event("mouseenter"));

    expect(items[0].classList.contains("is-active")).toBe(false);
    expect(keyboardItem.classList.contains("is-active")).toBe(true);

    const label = document.getElementById("mega-preview-cat-label");
    const price = document.getElementById("mega-preview-price-val");
    const chips = document.getElementById("mega-preview-brand-chips");
    const budget = document.getElementById("mega-preview-budget-link");
    const view = document.getElementById("mega-preview-view-link");

    expect(label.textContent).toBe("Keyboards & Mice");
    expect(price.textContent).toBe("₹799");
    expect(budget.textContent).toContain("Under ₹999");
    expect(budget.getAttribute("href")).toBe("/c/keyboards/?max_price=999");
    expect(view.getAttribute("href")).toBe("/c/keyboards/");

    const chipLinks = chips.querySelectorAll(".mega-brand-chip");
    expect(chipLinks.length).toBe(2);
    expect(chipLinks[0].textContent).toBe("Logitech");
    expect(chipLinks[1].textContent).toBe("Keychron");
  });

  it("supports ArrowUp and ArrowDown navigation", () => {
    initMenuPanel();
    const catList = document.querySelector(".mega-menu-cat-list");
    const items = document.querySelectorAll(".mega-menu-cat-item");
    const firstFocus = vi.spyOn(items[0], "focus");
    const secondFocus = vi.spyOn(items[1], "focus");

    // Simulate focus on first item
    items[0].focus();
    catList.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    expect(secondFocus).toHaveBeenCalled();

    // From second item, ArrowUp moves to first
    items[1].focus();
    catList.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }));
    expect(firstFocus).toHaveBeenCalled();
  });
});
