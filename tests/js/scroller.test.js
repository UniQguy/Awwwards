import { describe, it, expect, beforeEach, vi } from "vitest";
import { shouldEnableLenis, initMotionToggleButton } from "../../frontend/js/modules/scroller.js";
import { STORAGE_KEY_USER_PREF } from "../../frontend/js/modules/capability.js";

describe("scroller.js - shouldEnableLenis guards", () => {
  beforeEach(() => {
    document.documentElement.dataset.motionTier = "1";
    document.body.dataset.layer = "editorial";
    window.innerWidth = 1280;
    delete window.location;
    window.location = new URL("http://localhost:8000/");

    // Mock matchMedia fine pointer
    window.matchMedia = vi.fn().mockImplementation((query) => {
      if (query === "(pointer: fine)") return { matches: true };
      if (query === "(prefers-reduced-motion: reduce)") return { matches: false };
      return { matches: false };
    });
  });

  it("returns true on editorial page with Tier 1 and desktop fine pointer", () => {
    expect(shouldEnableLenis()).toBe(true);
  });

  it("returns false if motion tier is not 1", () => {
    document.documentElement.dataset.motionTier = "2";
    expect(shouldEnableLenis()).toBe(false);

    document.documentElement.dataset.motionTier = "3";
    expect(shouldEnableLenis()).toBe(false);
  });

  it("returns false on coarse pointer devices (touch)", () => {
    window.matchMedia = vi.fn().mockImplementation((query) => {
      if (query === "(pointer: fine)") return { matches: false };
      return { matches: false };
    });
    expect(shouldEnableLenis()).toBe(false);
  });

  it("returns false on viewports under 1024px", () => {
    window.innerWidth = 768;
    expect(shouldEnableLenis()).toBe(false);
  });

  it("returns false if body is not marked with data-layer='editorial'", () => {
    delete document.body.dataset.layer;
    expect(shouldEnableLenis()).toBe(false);
  });

  it("returns false on utility paths even if other conditions match", () => {
    window.location = new URL("http://localhost:8000/cart/");
    expect(shouldEnableLenis()).toBe(false);

    window.location = new URL("http://localhost:8000/checkout/");
    expect(shouldEnableLenis()).toBe(false);

    window.location = new URL("http://localhost:8000/account/");
    expect(shouldEnableLenis()).toBe(false);
  });
});

describe("scroller.js - initMotionToggleButton", () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = `
      <button type="button" id="toggle-reduce-motion" aria-pressed="false">
        <span class="motion-toggle-label">Reduce motion: Off</span>
      </button>
    `;
    window.matchMedia = vi.fn().mockReturnValue({ matches: false });
  });

  it("toggles preference between reduced and auto when clicked", () => {
    initMotionToggleButton();
    const btn = document.getElementById("toggle-reduce-motion");
    const label = btn.querySelector(".motion-toggle-label");

    // Click 1: turn on reduced motion
    btn.click();
    expect(localStorage.getItem(STORAGE_KEY_USER_PREF)).toBe("reduced");
    expect(btn.getAttribute("aria-pressed")).toBe("true");
    expect(label.textContent).toBe("Reduce motion: On");

    // Click 2: turn off reduced motion
    btn.click();
    expect(localStorage.getItem(STORAGE_KEY_USER_PREF)).toBeNull();
    expect(btn.getAttribute("aria-pressed")).toBe("false");
    expect(label.textContent).toBe("Reduce motion: Off");
  });
});
