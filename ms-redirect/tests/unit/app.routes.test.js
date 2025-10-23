import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";

process.env.DDB_TABLE = "TestTable";
process.env.AWS_REGION = "us-east-1";

vi.mock("../../src/dynamo.js", () => {
  return {
    getLinkBySlug: vi.fn(),
    incrementMetrics: vi.fn().mockResolvedValue(undefined),
  };
});

import { getLinkBySlug, incrementMetrics } from "../../src/dynamo.js";
const { createApp } = await import("../../src/app.js");

describe("Rutas ms-redirect (AAA)", () => {
  let app;

  beforeEach(() => {
    vi.clearAllMocks();
    app = createApp();
  });

  it("GET /health => 200", async () => {
    // Arrange: (n/a extra)
    // Act
    const res = await request(app).get("/health");
    // Assert
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ ok: true });
  });

  it("GET /:slug => 404 si no existe", async () => {
    // Arrange
    getLinkBySlug.mockResolvedValueOnce(null);

    // Act
    const res = await request(app).get("/nope");

    // Assert
    expect(res.status).toBe(404);
    expect(res.body).toEqual({ error: "Not found" });
    expect(incrementMetrics).not.toHaveBeenCalled();
  });

  it("GET /:slug => 302 redirect y registra métricas con headers CF", async () => {
    // Arrange
    getLinkBySlug.mockResolvedValueOnce({ destinationUrl: "https://example.com" });

    // Act
    const res = await request(app)
      .get("/promo")
      .set("cloudfront-viewer-country", "co")
      .set("cloudfront-is-mobile-viewer", "true");

    // Assert
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe("https://example.com");
    expect(incrementMetrics).toHaveBeenCalledWith({
      slug: "promo",
      variant: "default",
      country: "CO",
      device: "mobile",
    });
  });

  it("GET /:slug/:variant => 302 y usa el variant del path", async () => {
    // Arrange
    getLinkBySlug.mockResolvedValueOnce({ destinationUrl: "https://e.com" });

    // Act
    const res = await request(app)
      .get("/promo/A1")
      .set("cloudfront-viewer-country", "us")
      .set("cloudfront-is-desktop-viewer", "true");

    // Assert
    expect(res.status).toBe(302);
    expect(res.headers.location).toBe("https://e.com");
    expect(incrementMetrics).toHaveBeenCalledWith({
      slug: "promo",
      variant: "A1",
      country: "US",
      device: "desktop",
    });
  });
});
