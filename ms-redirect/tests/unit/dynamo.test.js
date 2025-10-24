import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";

const h = vi.hoisted(() => ({
  ctorSpy: vi.fn(),
}));

const realEnv = { ...process.env };

beforeEach(() => {
  vi.restoreAllMocks();
  process.env = { ...realEnv };
});

describe("dynamo.js init (al importar)", () => {
  it("falla y hace exit(1) si falta DDB_TABLE", async () => {
    vi.resetModules();
    delete process.env.DDB_TABLE;
    process.env.AWS_REGION = "us-east-1";

    const exitSpy = vi
      .spyOn(process, "exit")
      .mockImplementation(() => {
        throw new Error("exit");
      });
    const errSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    vi.mock("@aws-sdk/client-dynamodb", () => ({
      DynamoDBClient: class { constructor() {} },
    }));
    vi.mock("@aws-sdk/lib-dynamodb", () => ({
      DynamoDBDocumentClient: { from: () => ({ send: vi.fn() }) },
      GetCommand: class {},
      UpdateCommand: class {},
    }));

    await expect(import("../../src/dynamo.js")).rejects.toThrow("exit");
    expect(errSpy).toHaveBeenCalledWith("[ms-redirect] Falta DDB_TABLE en el .env");
    expect(exitSpy).toHaveBeenCalledWith(1);
  });

  it("pasa endpoint cuando DDB_ENDPOINT está definido", async () => {
    vi.resetModules();
    process.env.DDB_TABLE = "TestTable";
    process.env.AWS_REGION = "us-east-1";
    process.env.DDB_ENDPOINT = "http://localhost:4566";

    h.ctorSpy.mockClear();
    vi.mock("@aws-sdk/client-dynamodb", () => ({
      DynamoDBClient: class {
        constructor(cfg) {
          h.ctorSpy(cfg);
        }
      },
    }));
    vi.mock("@aws-sdk/lib-dynamodb", () => ({
      DynamoDBDocumentClient: { from: () => ({ send: vi.fn() }) },
      GetCommand: class {},
      UpdateCommand: class {},
    }));

    await import("../../src/dynamo.js");
    expect(h.ctorSpy).toHaveBeenCalledTimes(1);
    const cfg = h.ctorSpy.mock.calls[0][0];
    expect(cfg).toMatchObject({
      region: "us-east-1",
      endpoint: "http://localhost:4566",
    });
  });

  it("configura credentials cuando hay AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY", async () => {
    vi.resetModules();
    process.env.DDB_TABLE = "TestTable";
    process.env.AWS_REGION = "us-east-1";
    process.env.AWS_ACCESS_KEY_ID = "AKIA_TEST";
    process.env.AWS_SECRET_ACCESS_KEY = "SECRET_TEST";

    h.ctorSpy.mockClear();
    vi.mock("@aws-sdk/client-dynamodb", () => ({
      DynamoDBClient: class {
        constructor(cfg) {
          h.ctorSpy(cfg);
        }
      },
    }));
    vi.mock("@aws-sdk/lib-dynamodb", () => ({
      DynamoDBDocumentClient: { from: () => ({ send: vi.fn() }) },
      GetCommand: class {},
      UpdateCommand: class {},
    }));

    await import("../../src/dynamo.js");
    const cfg = h.ctorSpy.mock.calls[0][0];
    expect(cfg.credentials).toEqual({
      accessKeyId: "AKIA_TEST",
      secretAccessKey: "SECRET_TEST",
    });
  });
});

describe("dynamo.js runtime", () => {
  let ddb;
  let getLinkBySlug;
  let incrementMetrics;

  beforeAll(async () => {
    vi.resetModules();
    vi.doUnmock?.("@aws-sdk/client-dynamodb");
    vi.doUnmock?.("@aws-sdk/lib-dynamodb");

    process.env.DDB_TABLE = "TestTable";
    process.env.AWS_REGION = "us-east-1";
    delete process.env.DDB_ENDPOINT;
    delete process.env.AWS_ACCESS_KEY_ID;
    delete process.env.AWS_SECRET_ACCESS_KEY;

    const dynamo = await import("../../src/dynamo.js");
    ddb = dynamo.ddb;
    getLinkBySlug = dynamo.getLinkBySlug;
    incrementMetrics = dynamo.incrementMetrics;
  });

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("getLinkBySlug => null si no hay Item", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({ Item: undefined });
    const result = await getLinkBySlug("abc");
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toBeNull();
  });

  it("getLinkBySlug => null si enabled === false", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({ Item: { enabled: false } });
    const result = await getLinkBySlug("abc");
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toBeNull();
  });

  it("getLinkBySlug => destinationUrl si existe y enabled !== false", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({
      Item: { enabled: true, destinationUrl: "https://x.com" },
    });
    const result = await getLinkBySlug("abc");
    expect(sendSpy).toHaveBeenCalledTimes(1);
    expect(result).toEqual({ destinationUrl: "https://x.com" });
  });

  it("incrementMetrics => hace un único UPDATE con los parámetros indicados", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({});

    await incrementMetrics({
      slug: "promo",
      variant: "B",
      country: "co",
      device: "mobile",
    });

    expect(sendSpy).toHaveBeenCalledTimes(1);
    const cmd = sendSpy.mock.calls[0][0];

    expect(cmd.input.TableName).toBe("TestTable");
    expect(cmd.input.Key).toEqual({ PK: "METRIC#promo#B", SK: "TOTAL" });
    expect(cmd.input.ExpressionAttributeNames).toEqual({ "#c": "CO", "#d": "mobile" });
    expect(cmd.input.ExpressionAttributeValues).toMatchObject({
      ":one": 1,
      ":zero": 0,
      ":empty": {},
    });
    expect(cmd.input.UpdateExpression).toContain("ADD clicks :one");
    expect(cmd.input.UpdateExpression).toContain("byCountry = if_not_exists(byCountry, :empty)");
    expect(cmd.input.UpdateExpression).toContain("byDevice = if_not_exists(byDevice, :empty)");
    expect(cmd.input.ReturnValues).toBe("NONE");
  });

  it("incrementMetrics => usa defaults (variant=default, country=UN, device=unknown)", async () => {
    const sendSpy = vi.spyOn(ddb, "send").mockResolvedValueOnce({}); // UPDATE ok

    await incrementMetrics({ slug: "promo" });

    expect(sendSpy).toHaveBeenCalledTimes(1);
    const cmd = sendSpy.mock.calls[0][0];

    expect(cmd.input.Key).toEqual({ PK: "METRIC#promo#default", SK: "TOTAL" });
    expect(cmd.input.ExpressionAttributeNames).toEqual({ "#c": "UN", "#d": "unknown" });
  });
});
