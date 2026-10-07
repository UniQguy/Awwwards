import { describe, it, expect } from "vitest";
import { calculateTilt, resetTilt } from "../../frontend/js/modules/collectible_cards.js";

describe("collectible_cards.js - Tilt Math and Clamping", () => {
  const fakeRect = {
    left: 100,
    top: 100,
    width: 200,
    height: 200,
  };

  it("returns zero rotation when pointer is precisely at the center", () => {
    // Center of fakeRect is (200, 200)
    const result = calculateTilt(fakeRect, 200, 200, 6);
    expect(result.rotateX).toBe(0);
    expect(result.rotateY).toBe(0);
    expect(result.glareX).toBe(50);
    expect(result.glareY).toBe(50);
    expect(result.glareOpacity).toBe(0);
  });

  it("calculates correct pitch and yaw at top-left corner", () => {
    // Top-left is (100, 100): dx = -1, dy = -1 -> rotateX = +6, rotateY = -6
    const result = calculateTilt(fakeRect, 100, 100, 6);
    expect(result.rotateX).toBe(6);
    expect(result.rotateY).toBe(-6);
    expect(result.glareX).toBe(0);
    expect(result.glareY).toBe(0);
    expect(result.glareOpacity).toBeGreaterThan(0);
  });

  it("calculates correct pitch and yaw at bottom-right corner", () => {
    // Bottom-right is (300, 300): dx = +1, dy = +1 -> rotateX = -6, rotateY = +6
    const result = calculateTilt(fakeRect, 300, 300, 6);
    expect(result.rotateX).toBe(-6);
    expect(result.rotateY).toBe(6);
    expect(result.glareX).toBe(100);
    expect(result.glareY).toBe(100);
  });

  it("clamps pointer coordinates that exceed card bounds", () => {
    // Extreme far left and top (-500, -500)
    const result = calculateTilt(fakeRect, -500, -500, 6);
    expect(result.rotateX).toBe(6);
    expect(result.rotateY).toBe(-6);
    expect(result.glareX).toBe(0);
    expect(result.glareY).toBe(0);
  });

  it("gracefully returns reset values on empty or missing rect", () => {
    expect(calculateTilt(null, 10, 10)).toEqual(resetTilt());
    expect(calculateTilt({ left: 0, top: 0, width: 0, height: 0 }, 10, 10)).toEqual(resetTilt());
  });

  it("resetTilt returns flat neutral orientation", () => {
    const neutral = resetTilt();
    expect(neutral.rotateX).toBe(0);
    expect(neutral.rotateY).toBe(0);
    expect(neutral.glareOpacity).toBe(0);
  });
});
