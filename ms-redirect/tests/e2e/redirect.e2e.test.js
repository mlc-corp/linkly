import { describe, it, expect } from "vitest";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, GetCommand } from "@aws-sdk/lib-dynamodb";

// Helpers
const APP = process.env.APP_BASE_URL || "http://localhost:8080";
const DDB_ENDPOINT = process.env.DDB_ENDPOINT || "http://localhost:8000";
const DDB_TABLE = process.env.DDB_TABLE || "LinklyTable";
const REGION = process.env.AWS_REGION || "us-east-1";

// Cliente DDB para asserts E2E
const ddbDoc = DynamoDBDocumentClient.from(
  new DynamoDBClient({
    region: REGION,
    endpoint: DDB_ENDPOINT,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || "fake",
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "fake",
    },
  }),
  { marshallOptions: { removeUndefinedValues: true } }
);

async function getMetric(slug, variant = "default") {
  const out = await ddbDoc.send(
    new GetCommand({
      TableName: DDB_TABLE,
      Key: { PK: `METRIC#${slug}#${variant}`, SK: "TOTAL" },
      ConsistentRead: true,
    })
  );
  return out.Item;
}

describe("E2E ms-redirect (AAA)", () => {
  it("debería responder /health OK y redirigir /promo con métrica incrementada", async () => {
    // ------------------------
    // Arrange
    // ------------------------
    const slug = "promo";
    const variant = "default";
    const before = await getMetric(slug, variant);
    const prevClicks = before?.clicks || 0;

    // ------------------------
    // Act
    // ------------------------
    const res = await fetch(`${APP}/promo`, {
      method: "GET",
      headers: {
        "cloudfront-viewer-country": "co",
        "cloudfront-is-mobile-viewer": "true",
      },
      redirect: "manual",
    });

    // ------------------------
    // Assert
    // ------------------------
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe("https://example.com");

    await new Promise(r => setTimeout(r, 150));

    const after = await getMetric(slug, variant);
    expect(after).toBeDefined();
    expect(after.clicks).toBe(prevClicks + 1);
    expect(after.byCountry?.CO).toBeDefined();
    expect(after.byDevice?.mobile).toBeDefined();
  });

  it("debería responder /health con 200", async () => {
    // Arrange (n/a)
    // Act
    const res = await fetch(`${APP}/health`);
    // Assert
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual({ ok: true });
  });
});
