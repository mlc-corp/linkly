import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";

process.env.DDB_TABLE = "TestTable";
process.env.AWS_REGION = "us-east-1";

let ddb;
let getLinkBySlug;
let incrementMetrics;

beforeAll(async () => {
  const dynamo = await import("../../src/dynamo.js");
  ddb = dynamo.ddb;
  getLinkBySlug = dynamo.getLinkBySlug;
  incrementMetrics = dynamo.incrementMetrics;
});

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("dynamo.js (AAA)", () => {
  it("getLinkBySlug => null si no hay Item", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({ Item: undefined });
    const result = await getLinkBySlug("abc");
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toBeNull();
  });

  it("getLinkBySlug => null si enabled === false", async () => {
    // Arrange
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({ Item: { enabled: false } });

    // Act
    const result = await getLinkBySlug("abc");

    // Assert
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toBeNull();
  });

  it("getLinkBySlug => destinationUrl si existe y enabled !== false", async () => {
    // Arrange
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({
      Item: { enabled: true, destinationUrl: "https://x.com" },
    });

    // Act
    const result = await getLinkBySlug("abc");

    // Assert
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toEqual({ destinationUrl: "https://x.com" });
  });

  it("incrementMetrics => UPDATE directo cuando la fila existe", async () => {
    // Arrange
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({}); // UPDATE ok

    // Act
    await incrementMetrics({
      slug: "promo",
      variant: "B",
      country: "co",
      device: "mobile",
    });

    // Assert
    expect(sendSpy).toHaveBeenCalledTimes(1);
  });

  it("incrementMetrics => inicializa y reintenta si falla la primera vez", async () => {
    // Arrange
    const firstError = new Error("no existe");
    firstError.name = "ConditionalCheckFailedException";
    const sendSpy = vi.spyOn(ddb, "send");

    // 1) Primer UPDATE falla (fila inexistente)
    sendSpy.mockRejectedValueOnce(firstError);
    // 2) initMetricIfAbsent (UPDATE con ConditionExpression) resuelve ok
    sendSpy.mockResolvedValueOnce({});
    // 3) Segundo UPDATE (retry) resuelve ok
    sendSpy.mockResolvedValueOnce({});

    // Act
    await incrementMetrics({
      slug: "promo",
      variant: undefined, // default -> "default"
      country: undefined, // default -> "UN"
      device: undefined,  // default -> "unknown"
    });

    // Assert
    expect(sendSpy).toHaveBeenCalledTimes(3);
  });
});
