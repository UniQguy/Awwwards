/**
 * Privacy-first Recently Viewed objects manager (WP5).
 * Stores last viewed items in client-side localStorage only (no cookies, no external telemetry).
 */

const STORAGE_KEY = "electrocart_recently_viewed";
const MAX_RECENT_ITEMS = 6;

export function initRecentlyViewed() {
  if (typeof window === "undefined" || !window.localStorage) return;

  // 1. If on PDP, record the current product
  const trackerEl = document.querySelector("[data-product-track]");
  let currentId = null;
  if (trackerEl) {
    currentId = trackerEl.dataset.productId;
    const item = {
      id: trackerEl.dataset.productId,
      slug: trackerEl.dataset.productSlug,
      name: trackerEl.dataset.productName,
      price: trackerEl.dataset.productPrice,
      image: trackerEl.dataset.productImage,
      category: trackerEl.dataset.productCategory,
    };
    saveItem(item);
  }

  // 2. Render recently viewed items if container exists
  renderRecentlyViewed(currentId);
}

function saveItem(newItem) {
  if (!newItem.id || !newItem.name) return;
  try {
    let items = getStoredItems();
    // Remove if already present so it moves to front
    items = items.filter((it) => it.id !== newItem.id);
    items.unshift(newItem);
    if (items.length > MAX_RECENT_ITEMS) {
      items = items.slice(0, MAX_RECENT_ITEMS);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch (_) {
    // Storage quota or disabled in private browsing
  }
}

function getStoredItems() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (_) {
    return [];
  }
}

function renderRecentlyViewed(excludeId) {
  const container = document.getElementById("recently-viewed-grid");
  const section = document.getElementById("recently-viewed-section");
  if (!container || !section) return;

  let items = getStoredItems();
  if (excludeId) {
    items = items.filter((it) => it.id !== excludeId);
  }

  if (items.length === 0) {
    section.style.display = "none";
    return;
  }

  container.innerHTML = items
    .map(
      (item) => `
    <div class="product-card-container">
      <article class="product-card">
        <a href="/p/${escapeHtml(item.slug)}/" class="stretched-link" aria-label="${escapeHtml(item.name)}"></a>
        <div class="product-plate">
          ${
            item.image
              ? `<img src="${escapeHtml(item.image)}" alt="${escapeHtml(item.name)}" width="240" height="180" loading="lazy" style="max-width: 100%; max-height: 100%; object-fit: contain;">`
              : `<div class="image-fallback-plate" role="img"><span class="image-fallback-initial">${escapeHtml(item.name.slice(0, 1))}</span></div>`
          }
        </div>
        <div class="card-body">
          <span class="card-brand">${escapeHtml(item.category || "Electronics")}</span>
          <h3 class="card-title">${escapeHtml(item.name)}</h3>
          <div class="price-row mt-1">
            <span class="price-current">${escapeHtml(item.price)}</span>
          </div>
          <span class="card-arrow-glyph" aria-hidden="true">&rarr;</span>
        </div>
      </article>
    </div>
  `
    )
    .join("");

  section.style.display = "block";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
