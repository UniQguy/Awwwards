import { describe, it, expect } from "vitest";
import { canCycleCutouts, getNextCycleIndex } from "../../frontend/js/modules/headline_cutouts.js";

describe("headline_cutouts.js - Scheduler and State Guards", () => {
  const baseIdealState = {
    tier: 1,
    isHidden: false,
    isIntersecting: true,
    isHovered: false,
    isReducedMotion: false,
  };

  it("permits cutout cycling on Tier 1 in ideal conditions", () => {
    expect(canCycleCutouts(baseIdealState)).toBe(true);
  });

  it("permits cutout cycling on Tier 2 in ideal conditions", () => {
    expect(canCycleCutouts({ ...baseIdealState, tier: 2 })).toBe(true);
  });

  it("STOPS cutout cycling on Tier 3", () => {
    expect(canCycleCutouts({ ...baseIdealState, tier: 3 })).toBe(false);
  });

  it("STOPS cutout cycling under prefers-reduced-motion", () => {
    expect(canCycleCutouts({ ...baseIdealState, isReducedMotion: true })).toBe(false);
  });

  it("STOPS cutout cycling when document is hidden (background tab)", () => {
    expect(canCycleCutouts({ ...baseIdealState, isHidden: true })).toBe(false);
  });

  it("STOPS cutout cycling when hero is offscreen (!isIntersecting)", () => {
    expect(canCycleCutouts({ ...baseIdealState, isIntersecting: false })).toBe(false);
  });

  it("STOPS cutout cycling when user is hovering or focusing inside the hero", () => {
    expect(canCycleCutouts({ ...baseIdealState, isHovered: true })).toBe(false);
  });
});

describe("headline_cutouts.js - Circular buffer indexing", () => {
  it("increments index with modulo wrap-around", () => {
    expect(getNextCycleIndex(0, 5, 1)).toBe(1);
    expect(getNextCycleIndex(4, 5, 1)).toBe(0);
    expect(getNextCycleIndex(2, 5, 3)).toBe(0); // (2 + 3) % 5 = 0
  });

  it("safely handles total <= 0", () => {
    expect(getNextCycleIndex(0, 0, 1)).toBe(0);
    expect(getNextCycleIndex(2, -1, 1)).toBe(0);
  });
});
