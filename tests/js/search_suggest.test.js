import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { initSearchSuggest } from "../../frontend/js/modules/search-suggest.js";

describe("search-suggest.js", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    document.body.innerHTML = `
      <form class="header-search-form" action="/search/" method="get" role="search">
        <input
          type="search"
          id="site-search-input"
          name="q"
          class="header-search-input"
          autocomplete="off"
          role="combobox"
          aria-expanded="false"
          aria-haspopup="listbox"
          aria-controls="search-suggestions-list"
          aria-autocomplete="list"
        />
        <div id="search-suggestions-container" class="search-suggestions-container" hidden>
          <ul id="search-suggestions-list" class="search-suggestions-list" role="listbox" aria-label="Search suggestions"></ul>
        </div>
      </form>
    `;
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("does not fetch if input has fewer than 2 characters", () => {
    initSearchSuggest();
    const input = document.getElementById("site-search-input");
    input.value = "h";
    input.dispatchEvent(new Event("input"));

    vi.advanceTimersByTime(200);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("fetches suggestions with 150ms debounce and populates list", async () => {
    const mockData = {
      categories: [{ name: "Headphones", slug: "headphones" }],
      brands: ["Sony"],
      products: [{ id: 1, display_name: "Sony WH-1000XM4", slug: "sony-wh-1000xm4", selling_price: "24990" }],
    };

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockData,
    });

    initSearchSuggest();
    const input = document.getElementById("site-search-input");
    const container = document.getElementById("search-suggestions-container");
    const list = document.getElementById("search-suggestions-list");

    input.value = "head";
    input.dispatchEvent(new Event("input"));

    await vi.advanceTimersByTimeAsync(160);

    expect(container.hidden).toBe(false);
    expect(input.getAttribute("aria-expanded")).toBe("true");

    const items = list.querySelectorAll(".suggestion-item");
    // 1 category + 1 brand + 1 product + 1 see all = 4 items
    expect(items.length).toBe(4);
  });

  it("supports keyboard navigation with ArrowDown, ArrowUp, and Escape", async () => {
    const mockData = {
      categories: [{ name: "Headphones", slug: "headphones" }],
      brands: [],
      products: [{ id: 1, display_name: "Sony WH-1000XM4", slug: "sony-wh-1000xm4", selling_price: "24990" }],
    };

    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockData,
    });

    initSearchSuggest();
    const input = document.getElementById("site-search-input");
    const container = document.getElementById("search-suggestions-container");
    const list = document.getElementById("search-suggestions-list");

    input.value = "head";
    input.dispatchEvent(new Event("input"));
    await vi.advanceTimersByTimeAsync(160);
    await Promise.resolve();
    await Promise.resolve();

    expect(container.hidden).toBe(false);
    expect(list.children.length).toBeGreaterThan(0);

    // Arrow down to first item
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    expect(input.getAttribute("aria-activedescendant")).toBe("suggestion-opt-0");
    const firstItem = list.querySelector("#suggestion-opt-0");
    expect(firstItem.getAttribute("aria-selected")).toBe("true");

    // Arrow down to second item
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }));
    expect(input.getAttribute("aria-activedescendant")).toBe("suggestion-opt-1");

    // Arrow up back to first item
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowUp" }));
    expect(input.getAttribute("aria-activedescendant")).toBe("suggestion-opt-0");

    // Escape closes suggestions
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(container.hidden).toBe(true);
    expect(input.getAttribute("aria-expanded")).toBe("false");
    expect(input.hasAttribute("aria-activedescendant")).toBe(false);
  });
});
