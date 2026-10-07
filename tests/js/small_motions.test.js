import { describe, it, expect, beforeEach, vi } from "vitest";
import { initSmallMotions, announceBagUpdate } from "../../frontend/js/modules/small_motions.js";

describe("small_motions.js - Bag announcer and badge nudge", () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="live-announcer" aria-live="polite"></div>
      <span class="header-bag-count">0</span>
      <span class="nav-bag-count">0</span>
    `;
    document.documentElement.dataset.motionTier = "1";
    vi.useFakeTimers();
  });

  it("updates live announcer text politely", () => {
    announceBagUpdate("Item added to bag (1 item)", 1);
    vi.advanceTimersByTime(60);

    const announcer = document.getElementById("live-announcer");
    expect(announcer.textContent).toBe("Item added to bag (1 item)");

    const headerBadge = document.querySelector(".header-bag-count");
    expect(headerBadge.textContent).toBe("1");
    expect(headerBadge.classList.contains("bag-count-nudge")).toBe(true);
  });

  it("does not add animation class on Tier 3", () => {
    document.documentElement.dataset.motionTier = "3";
    announceBagUpdate("Added", 2);
    vi.advanceTimersByTime(60);

    const headerBadge = document.querySelector(".header-bag-count");
    expect(headerBadge.textContent).toBe("2");
    expect(headerBadge.classList.contains("bag-count-nudge")).toBe(false);
  });
});
