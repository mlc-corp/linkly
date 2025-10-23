import { describe, it, expect } from "vitest";
import { extractContextFromCFHeaders } from "../src/metrics.js";

describe("extractContextFromCFHeaders (AAA)", () => {
  it("detecta mobile y país CO (normaliza mayúsculas)", () => {
    const req = {
      headers: {
        "cloudfront-viewer-country": "co",
        "cloudfront-is-mobile-viewer": "true",
      },
    };
    const ctx = extractContextFromCFHeaders(req);
    expect(ctx).toEqual({ country: "CO", device: "mobile" });
  });

  it("prioriza correctamente mobile sobre tablet si ambos vienen en headers", () => {
    // Arrange
    const req = {
      headers: {
        "cloudfront-viewer-country": "br",
        "cloudfront-is-tablet-viewer": "true",
        "cloudfront-is-mobile-viewer": "true",
      },
    };

    // Act
    const ctx = extractContextFromCFHeaders(req);

    // Assert
    expect(ctx.device).toBe("mobile");
    expect(ctx.country).toBe("BR");
  });

  it("usa defaults cuando no hay headers", () => {
    // Arrange
    const req = { headers: {} };

    // Act
    const ctx = extractContextFromCFHeaders(req);

    // Assert
    expect(ctx).toEqual({ country: "UN", device: "unknown" });
  });
});
