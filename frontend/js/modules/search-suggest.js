/**
 * Accessible, debounced typeahead suggestions combobox.
 * Adheres to WAI-ARIA 1.2 Combobox pattern with groups, thumbnails, and keyboard support.
 */

export function initSearchSuggest() {
  const input = document.querySelector("#site-search-input");
  const form = document.querySelector(".header-search-form");
  const container = document.querySelector("#search-suggestions-container");
  const list = document.querySelector("#search-suggestions-list");
  const progressBar = document.querySelector("#search-progress-bar");

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

  function highlightMatch(text, query) {
    if (!query) return escapeHTML(text);
    const escapedText = escapeHTML(text);
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(`(${escapedQuery})`, "gi");
    return escapedText.replace(regex, "<mark class='search-match'>$1</mark>");
  }

  function hideSuggestions() {
    container.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    if (progressBar) progressBar.hidden = true;
    activeIndex = -1;
    list.innerHTML = "";
    items = [];
  }

  function showSuggestions() {
    container.hidden = false;
    input.setAttribute("aria-expanded", "true");
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
    if (progressBar) progressBar.hidden = true;

    const rawCategories = data.categories || [];
    const rawBrands = data.brand_items || (data.brands || []).map((b) => (typeof b === "string" ? { name: b, url: `/search/?brand=${encodeURIComponent(b)}`, count: 0 } : b));
    const rawProducts = data.products || [];

    const builtItems = [];
    let html = "";

    // Categories group (max 2)
    if (rawCategories.length > 0) {
      html += `<li class="suggestion-group-label" role="presentation">Categories</li>`;
      rawCategories.slice(0, 2).forEach((cat) => {
        const itemIdx = builtItems.length;
        const countStr = cat.count !== undefined ? `<span class="suggestion-count">${cat.count}</span>` : "";
        builtItems.push({
          type: "category",
          title: cat.name,
          url: cat.url || `/c/${cat.slug}/`,
        });

        html += `
          <li
            id="suggestion-opt-${itemIdx}"
            class="suggestion-item suggestion-category"
            role="option"
            aria-selected="false"
            data-index="${itemIdx}"
            data-url="${escapeHTML(cat.url || `/c/${cat.slug}/`)}"
          >
            <span class="suggestion-title">${highlightMatch(cat.name, query)}</span>
            ${countStr}
          </li>
        `;
      });
    }

    // Brands group (max 3)
    if (rawBrands.length > 0) {
      html += `<li class="suggestion-group-label" role="presentation">Brands</li>`;
      rawBrands.slice(0, 3).forEach((b) => {
        const itemIdx = builtItems.length;
        const countStr = b.count ? `<span class="suggestion-count">${b.count}</span>` : "";
        builtItems.push({
          type: "brand",
          title: b.name,
          url: b.url || `/search/?brand=${encodeURIComponent(b.name)}`,
        });

        html += `
          <li
            id="suggestion-opt-${itemIdx}"
            class="suggestion-item suggestion-brand-row"
            role="option"
            aria-selected="false"
            data-index="${itemIdx}"
            data-url="${escapeHTML(b.url || `/search/?brand=${encodeURIComponent(b.name)}`)}"
          >
            <span class="suggestion-title">${highlightMatch(b.name, query)}</span>
            ${countStr}
          </li>
        `;
      });
    }

    // Products group (max 5)
    if (rawProducts.length > 0) {
      html += `<li class="suggestion-group-label" role="presentation">Products</li>`;
      rawProducts.slice(0, 5).forEach((prod) => {
        const itemIdx = builtItems.length;
        const formattedPrice = prod.selling_price ? `₹${Math.round(parseFloat(prod.selling_price)).toLocaleString("en-IN")}` : "";
        const thumbHtml = prod.image_url
          ? `<div class="suggestion-thumb-plate"><img src="${escapeHTML(prod.image_url)}" alt="" class="suggestion-thumb-img"></div>`
          : `<div class="suggestion-thumb-plate"><span class="suggestion-thumb-placeholder">EC</span></div>`;

        builtItems.push({
          type: "product",
          title: prod.display_name,
          url: prod.url || `/p/${prod.slug}/`,
        });

        html += `
          <li
            id="suggestion-opt-${itemIdx}"
            class="suggestion-item suggestion-product-row"
            role="option"
            aria-selected="false"
            data-index="${itemIdx}"
            data-url="${escapeHTML(prod.url || `/p/${prod.slug}/`)}"
          >
            ${thumbHtml}
            <div class="suggestion-prod-info">
              <span class="suggestion-title">${highlightMatch(prod.display_name, query)}</span>
              ${prod.parsed_brand ? `<span class="suggestion-brand-sub">${escapeHTML(prod.parsed_brand)}</span>` : ""}
            </div>
            ${formattedPrice ? `<span class="suggestion-price">${escapeHTML(formattedPrice)}</span>` : ""}
          </li>
        `;
      });
    }

    // Empty state
    if (builtItems.length === 0) {
      list.innerHTML = `
        <li class="suggestion-empty-state" role="presentation">
          Nothing found for &ldquo;${escapeHTML(query)}&rdquo;. Try a brand or a product type.
        </li>
      `;
      items = [];
      showSuggestions();
      return;
    }

    // "See all results" row
    const seeAllIdx = builtItems.length;
    builtItems.push({
      type: "all",
      title: `See all results for "${query}"`,
      url: `/search/?q=${encodeURIComponent(query)}`,
    });

    html += `
      <li
        id="suggestion-opt-${seeAllIdx}"
        class="suggestion-item suggestion-see-all"
        role="option"
        aria-selected="false"
        data-index="${seeAllIdx}"
        data-url="/search/?q=${encodeURIComponent(query)}"
      >
        <span class="suggestion-title">See all results for &ldquo;${escapeHTML(query)}&rdquo; &rarr;</span>
      </li>
    `;

    items = builtItems;
    activeIndex = -1;
    input.removeAttribute("aria-activedescendant");
    list.innerHTML = html;
    showSuggestions();
  }

  function fetchSuggestions(query) {
    if (abortController) {
      abortController.abort();
    }

    abortController = new AbortController();
    if (progressBar) progressBar.hidden = false;

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
        if (progressBar) progressBar.hidden = true;
        if (err.name !== "AbortError") {
          hideSuggestions();
        }
      });
  }

  // Handle typing with 150ms debounce
  input.addEventListener("input", () => {
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

  // Shortcut hint '/' binds to focus search field when not in another input
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
      e.preventDefault();
      input.focus();
      input.select();
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
