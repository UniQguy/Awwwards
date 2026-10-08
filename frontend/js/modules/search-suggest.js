/**
 * Accessible, debounced typeahead suggestions combobox.
 * Adheres to WAI-ARIA 1.2 Combobox pattern.
 */

export function initSearchSuggest() {
  const input = document.querySelector("#site-search-input");
  const form = document.querySelector(".header-search-form");
  const container = document.querySelector("#search-suggestions-container");
  const list = document.querySelector("#search-suggestions-list");

  if (!input || !form || !container || !list) return;

  let debounceTimer = null;
  let abortController = null;
  let items = [];
  let activeIndex = -1;
  let originalQuery = "";

  function escapeHTML(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function hideSuggestions() {
    container.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    activeIndex = -1;
    list.innerHTML = "";
    items = [];
  }

  function showSuggestions() {
    if (items.length > 0) {
      container.hidden = false;
      input.setAttribute("aria-expanded", "true");
    }
  }

  function setActiveItem(index) {
    const optionElements = list.querySelectorAll(".suggestion-item");
    optionElements.forEach((el) => {
      el.setAttribute("aria-selected", "false");
      el.classList.remove("is-selected");
    });

    activeIndex = index;

    if (activeIndex >= 0 && activeIndex < items.length) {
      const activeEl = optionElements[activeIndex];
      if (activeEl) {
        activeEl.setAttribute("aria-selected", "true");
        activeEl.classList.add("is-selected");
        input.setAttribute("aria-activedescendant", activeEl.id);
        if (typeof activeEl.scrollIntoView === "function") {
          activeEl.scrollIntoView({ block: "nearest" });
        }
      }
    } else {
      activeIndex = -1;
      input.removeAttribute("aria-activedescendant");
    }
  }

  function navigateTo(url) {
    if (url) {
      window.location.href = url;
    }
  }

  function renderSuggestions(data, query) {
    const rawCategories = data.categories || [];
    const rawBrands = data.brand_items || (data.brands || []).map((b) => (typeof b === "string" ? { name: b, url: `/search/?brand=${encodeURIComponent(b)}` } : b));
    const rawProducts = data.products || [];

    const builtItems = [];

    // Categories (up to 2)
    rawCategories.slice(0, 2).forEach((cat) => {
      builtItems.push({
        type: "category",
        title: cat.name,
        url: cat.url || `/c/${cat.slug}/`,
        tag: "Category",
      });
    });

    // Brands (up to 2)
    rawBrands.slice(0, 2).forEach((b) => {
      builtItems.push({
        type: "brand",
        title: b.name,
        url: b.url || `/search/?brand=${encodeURIComponent(b.name)}`,
        tag: "Brand",
      });
    });

    // Products (fill up to max 8 total items)
    const remainingSlots = Math.max(1, 8 - builtItems.length);
    rawProducts.slice(0, remainingSlots).forEach((prod) => {
      builtItems.push({
        type: "product",
        title: prod.display_name,
        url: prod.url || `/p/${prod.slug}/`,
        tag: "Product",
        price: prod.selling_price ? `₹${Math.round(parseFloat(prod.selling_price))}` : "",
      });
    });

    if (builtItems.length === 0) {
      hideSuggestions();
      return;
    }

    // Always append "See all results" row
    builtItems.push({
      type: "all",
      title: `See all results for "${query}"`,
      url: `/search/?q=${encodeURIComponent(query)}`,
      tag: "All",
    });

    items = builtItems;
    activeIndex = -1;
    input.removeAttribute("aria-activedescendant");

    list.innerHTML = items
      .map((item, idx) => {
        const id = `suggestion-opt-${idx}`;
        const isSeeAll = item.type === "all";
        const tagHtml = isSeeAll ? "" : `<span class="suggestion-tag">${escapeHTML(item.tag)}</span>`;
        const priceHtml = item.price ? `<span class="suggestion-price">${escapeHTML(item.price)}</span>` : "";
        const seeAllClass = isSeeAll ? " suggestion-see-all" : "";

        return `
          <li
            id="${id}"
            class="suggestion-item${seeAllClass}"
            role="option"
            aria-selected="false"
            data-index="${idx}"
            data-url="${escapeHTML(item.url)}"
          >
            ${tagHtml}
            <span class="suggestion-title">${escapeHTML(item.title)}</span>
            ${priceHtml}
          </li>
        `;
      })
      .join("");

    showSuggestions();
  }

  function fetchSuggestions(query) {
    if (abortController) {
      abortController.abort();
    }

    abortController = new AbortController();

    fetch(`/search/suggest/?q=${encodeURIComponent(query)}`, {
      signal: abortController.signal,
      headers: { Accept: "application/json" },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Search suggest request failed");
        return res.json();
      })
      .then((data) => {
        renderSuggestions(data, query);
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          hideSuggestions();
        }
      });
  }

  // Handle typing with 150ms debounce
  input.addEventListener("input", (e) => {
    const val = input.value.trim();
    originalQuery = val;

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    if (val.length < 2) {
      if (abortController) abortController.abort();
      hideSuggestions();
      return;
    }

    debounceTimer = setTimeout(() => {
      fetchSuggestions(val);
    }, 150);
  });

  // Handle keyboard navigation
  input.addEventListener("keydown", (e) => {
    if (container.hidden || items.length === 0) {
      if (e.key === "ArrowDown" && input.value.trim().length >= 2) {
        fetchSuggestions(input.value.trim());
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (activeIndex < items.length - 1) {
          setActiveItem(activeIndex + 1);
        } else {
          setActiveItem(0); // Wrap to top
        }
        break;

      case "ArrowUp":
        e.preventDefault();
        if (activeIndex > 0) {
          setActiveItem(activeIndex - 1);
        } else if (activeIndex === 0) {
          setActiveItem(-1); // Return to original query
        } else {
          setActiveItem(items.length - 1); // Wrap to bottom
        }
        break;

      case "Enter":
        if (activeIndex >= 0 && activeIndex < items.length) {
          e.preventDefault();
          navigateTo(items[activeIndex].url);
        }
        // If activeIndex is -1, let form submit naturally
        break;

      case "Escape":
        e.preventDefault();
        hideSuggestions();
        break;

      case "Tab":
        hideSuggestions();
        break;
    }
  });

  // Use mousedown so clicking a suggestion navigates BEFORE blur fires
  list.addEventListener("mousedown", (e) => {
    const itemEl = e.target.closest(".suggestion-item");
    if (!itemEl) return;
    e.preventDefault();
    const url = itemEl.getAttribute("data-url");
    navigateTo(url);
  });

  // Mouse hover highlights option
  list.addEventListener("mousemove", (e) => {
    const itemEl = e.target.closest(".suggestion-item");
    if (!itemEl) return;
    const idx = parseInt(itemEl.getAttribute("data-index"), 10);
    if (!isNaN(idx) && idx !== activeIndex) {
      setActiveItem(idx);
    }
  });

  // Close when clicking outside
  document.addEventListener("pointerdown", (e) => {
    if (!form.contains(e.target) && !container.contains(e.target)) {
      hideSuggestions();
    }
  });

  // Re-open on input focus if query exists and items were populated
  input.addEventListener("focus", () => {
    if (items.length > 0 && input.value.trim().length >= 2) {
      showSuggestions();
    }
  });
}
