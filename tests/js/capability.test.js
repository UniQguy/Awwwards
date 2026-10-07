import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  evaluateCapabilities,
  probeWebGL,
  applyMotionTier,
  setManualMotionPreference,
  STORAGE_KEY_USER_PREF,
  STORAGE_KEY_SESSION_TIER,
} from "../../frontend/js/modules/capability.js";

describe("capability.js - evaluateCapabilities (pure decision logic)", () => {
  const baseIdealEnv = {
    motionDebugParam: null,
    userPreference: null,
    prefersReducedMotion: false,
    saveData: false,
    effectiveType: "4g",
    deviceMemory: 8,
    hardwareConcurrency: 8,
    isCoarsePointer: false,
    viewportWidth: 1440,
    hasWebGL: true,
    medianFrameDelta: 16.6,
  };

  it("yields Tier 1 on high-spec desktop with fine pointer and WebGL", () => {
    const tier = evaluateCapabilities(baseIdealEnv);
    expect(tier).toBe(1);
  });

  describe("Dev Overrides (?motion=1|2|3)", () => {
    it("forces Tier 1 when motionDebugParam is '1'", () => {
      const env = { ...baseIdealEnv, prefersReducedMotion: true, motionDebugParam: "1" };
      expect(evaluateCapabilities(env)).toBe(1);
    });

    it("forces Tier 2 when motionDebugParam is '2'", () => {
      const env = { ...baseIdealEnv, motionDebugParam: "2" };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("forces Tier 3 when motionDebugParam is '3'", () => {
      const env = { ...baseIdealEnv, motionDebugParam: "3" };
      expect(evaluateCapabilities(env)).toBe(3);
    });
  });

  describe("Reduced Motion Invariants", () => {
    it("ALWAYS yields Tier 3 when OS prefers-reduced-motion is true", () => {
      const env = { ...baseIdealEnv, prefersReducedMotion: true };
      expect(evaluateCapabilities(env)).toBe(3);
    });

    it("ALWAYS yields Tier 3 when user persistent preference is 'reduced'", () => {
      const env = { ...baseIdealEnv, userPreference: "reduced" };
      expect(evaluateCapabilities(env)).toBe(3);
    });
  });

  describe("Network Constraints", () => {
    it("yields at most Tier 2 when saveData is enabled", () => {
      const env = { ...baseIdealEnv, saveData: true };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it.each(["slow-2g", "2g", "3g"])(
      "yields at most Tier 2 on slow connection '%s'",
      (effectiveType) => {
        const env = { ...baseIdealEnv, effectiveType };
        expect(evaluateCapabilities(env)).toBe(2);
      }
    );
  });

  describe("Hardware and Device Constraints", () => {
    it("yields at most Tier 2 when deviceMemory < 4 GB", () => {
      const env = { ...baseIdealEnv, deviceMemory: 2 };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("yields at most Tier 2 when hardwareConcurrency <= 2 cores", () => {
      const env = { ...baseIdealEnv, hardwareConcurrency: 2 };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("yields at most Tier 2 when pointer is coarse (touch device)", () => {
      const env = { ...baseIdealEnv, isCoarsePointer: true };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("yields at most Tier 2 when viewport width < 1024px", () => {
      const env = { ...baseIdealEnv, viewportWidth: 768 };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("yields at most Tier 2 when WebGL is unavailable", () => {
      const env = { ...baseIdealEnv, hasWebGL: false };
      expect(evaluateCapabilities(env)).toBe(2);
    });

    it("yields at most Tier 2 when frame deltas indicate dropped frames (median > 24ms)", () => {
      const env = { ...baseIdealEnv, medianFrameDelta: 28.5 };
      expect(evaluateCapabilities(env)).toBe(2);
    });
  });
});

describe("capability.js - DOM integration & State updates", () => {
  beforeEach(() => {
    document.documentElement.removeAttribute("data-motion-tier");
    localStorage.clear();
    sessionStorage.clear();
  });

  it("applyMotionTier sets dataset.motionTier and dispatches motiontierchange event", () => {
    let capturedTier = null;
    const handler = (e) => {
      capturedTier = e.detail.tier;
    };
    window.addEventListener("motiontierchange", handler);

    applyMotionTier(2);

    expect(document.documentElement.dataset.motionTier).toBe("2");
    expect(capturedTier).toBe(2);

    window.removeEventListener("motiontierchange", handler);
  });

  it("setManualMotionPreference saves preference to localStorage and updates state", () => {
    setManualMotionPreference("reduced");
    expect(localStorage.getItem(STORAGE_KEY_USER_PREF)).toBe("reduced");

    setManualMotionPreference("auto");
    expect(localStorage.getItem(STORAGE_KEY_USER_PREF)).toBeNull();
  });
});

describe("capability.js - probeWebGL", () => {
  it("safely handles canvas context loss or missing canvas without throwing", () => {
    const fakeCanvas = {
      getContext: vi.fn().mockReturnValue(null),
    };
    expect(probeWebGL(fakeCanvas)).toBe(false);

    const loseContextMock = vi.fn();
    const fakeWorkingCanvas = {
      getContext: vi.fn().mockReturnValue({
        getExtension: vi.fn().mockReturnValue({
          loseContext: loseContextMock,
        }),
      }),
    };
    expect(probeWebGL(fakeWorkingCanvas)).toBe(true);
    expect(loseContextMock).toHaveBeenCalled();
  });
});
