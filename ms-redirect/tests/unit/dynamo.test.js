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

  it("incrementMetrics => hace un único UPDATE con los parámetros indicados", async () => {
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

    const cmd = sendSpy.mock.calls[0][0]; // UpdateCommand
    // Verifica la clave y nombres calculados
    expect(cmd.input.TableName).toBe("TestTable");
    expect(cmd.input.Key).toEqual({ PK: "METRIC#promo#B", SK: "TOTAL" });
    expect(cmd.input.ExpressionAttributeNames).toEqual({ "#c": "CO", "#d": "mobile" });
    expect(cmd.input.ExpressionAttributeValues).toMatchObject({ ":one": 1, ":zero": 0 });
    expect(cmd.input.UpdateExpression).toContain("ADD clicks :one");
    // Asegura que inicializa mapas si no existen
    expect(cmd.input.UpdateExpression).toContain("byCountry = if_not_exists(byCountry, :empty)");
    expect(cmd.input.UpdateExpression).toContain("byDevice = if_not_exists(byDevice, :empty)");
  });

  it("incrementMetrics => usa defaults (variant=default, country=UN, device=unknown)", async () => {
    // Arrange
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({}); // UPDATE ok

    // Act
    await incrementMetrics({
      slug: "promo",
      // variant/country/device omitidos -> defaults
    });

    // Assert
    expect(sendSpy).toHaveBeenCalledTimes(1);

    const cmd = sendSpy.mock.calls[0][0];
    expect(cmd.input.Key).toEqual({ PK: "METRIC#promo#default", SK: "TOTAL" });
    expect(cmd.input.ExpressionAttributeNames).toEqual({ "#c": "UN", "#d": "unknown" });
  });
});
