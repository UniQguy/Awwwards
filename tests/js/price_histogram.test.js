import { describe, it, expect } from "vitest";
import {
  formatINR,
  findNearestStepIndex,
  indexToPercent,
  percentToIndex,
  STEP_POINTS,
} from "../../frontend/js/modules/price_histogram.js";

describe("price_histogram.js - formatINR", () => {
  it("formats numbers with Indian grouping and Rupee symbol", () => {
    expect(formatINR(0)).toBe("₹0");
    expect(formatINR(500)).toBe("₹500");
    expect(formatINR(1000)).toBe("₹1,000");
    expect(formatINR(25000)).toBe("₹25,000");
    expect(formatINR(100000)).toBe("₹1,00,000");
    expect(formatINR(150000)).toBe("₹1,50,000");
  });

  it("handles null or NaN gracefully", () => {
    expect(formatINR(null)).toBe("₹0");
    expect(formatINR(NaN)).toBe("₹0");
  });
});

describe("price_histogram.js - Step Mapping & Conversions", () => {
  it("finds the exact index for known step points", () => {
    expect(findNearestStepIndex(0)).toBe(0);
    expect(findNearestStepIndex(500)).toBe(2);
    expect(findNearestStepIndex(10000)).toBe(11);
    expect(findNearestStepIndex(150000)).toBe(STEP_POINTS.length - 1);
  });

  it("finds the nearest index for values between steps", () => {
    // 600 is closer to 500 (index 2) than 750 (index 3)
    expect(findNearestStepIndex(600)).toBe(2);
    // 700 is closer to 750 (index 3) than 500 (index 2)
    expect(findNearestStepIndex(700)).toBe(3);
  });

  it("converts index to percent and back accurately", () => {
    expect(indexToPercent(0)).toBe(0);
    expect(indexToPercent(STEP_POINTS.length - 1)).toBe(100);

    const midIdx = Math.floor(STEP_POINTS.length / 2);
    const pct = indexToPercent(midIdx);
    const backIdx = percentToIndex(pct);
    expect(backIdx).toBe(midIdx);
  });

  it("clamps percentToIndex within valid boundaries", () => {
    expect(percentToIndex(-50)).toBe(0);
    expect(percentToIndex(150)).toBe(STEP_POINTS.length - 1);
  });
});
