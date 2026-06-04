import { verifyDimension } from "../src/dimension-check.js";

describe("verifyDimension", () => {
  it("passes when the dimension matches", () => {
    expect(() => verifyDimension(new Array(1536).fill(0.1), 1536)).not.toThrow();
  });

  it("throws naming both the actual and expected values", () => {
    expect(() => verifyDimension(new Array(384).fill(0.1), 1536)).toThrow(/384/);
    expect(() => verifyDimension(new Array(384).fill(0.1), 1536)).toThrow(/1536/);
  });

  it("throws on an empty vector", () => {
    expect(() => verifyDimension([], 1536)).toThrow();
  });
});
