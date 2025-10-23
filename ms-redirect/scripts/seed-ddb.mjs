import "dotenv/config";
import {
  DynamoDBClient,
  DescribeTableCommand,
  CreateTableCommand,
  ListTablesCommand,
} from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

const REGION = process.env.AWS_REGION || "us-east-1";
const ENDPOINT = process.env.DDB_ENDPOINT || "http://localhost:8000";
const TABLE = process.env.DDB_TABLE || "LinklyTable";
const ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID || "fake";
const SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY || "fake";

const base = new DynamoDBClient({
  region: REGION,
  endpoint: ENDPOINT,
  credentials: { accessKeyId: ACCESS_KEY_ID, secretAccessKey: SECRET_ACCESS_KEY },
});
const ddb = DynamoDBDocumentClient.from(base, { marshallOptions: { removeUndefinedValues: true } });

async function waitForDynamo(timeoutMs = 30000) {
  const start = Date.now();
  let attempt = 0;

  while (true) {
    try {
      await base.send(new ListTablesCommand({ Limit: 1 }));
      return;
    } catch (err) {
      if (Date.now() - start > timeoutMs) {
        throw new Error(`Timeout esperando DynamoDB en ${ENDPOINT}: ${err?.message || err}`);
      }
      const backoff = Math.min(1000, 200 + attempt * 100);
      await new Promise((r) => setTimeout(r, backoff));
      attempt += 1;
    }
  }
}

async function ensureTable() {
  try {
    await base.send(new DescribeTableCommand({ TableName: TABLE }));
    return;
  } catch (err) {
    if (err?.name !== "ResourceNotFoundException") throw err;
  }

  await base.send(new CreateTableCommand({
    TableName: TABLE,
    AttributeDefinitions: [
      { AttributeName: "PK", AttributeType: "S" },
      { AttributeName: "SK", AttributeType: "S" },
    ],
    KeySchema: [
      { AttributeName: "PK", KeyType: "HASH" },
      { AttributeName: "SK", KeyType: "RANGE" },
    ],
    BillingMode: "PAY_PER_REQUEST",
  }));

  const start = Date.now();
  while (true) {
    const { Table } = await base.send(new DescribeTableCommand({ TableName: TABLE }));
    if (Table?.TableStatus === "ACTIVE") break;
    if (Date.now() - start > 30000) throw new Error("Timeout esperando tabla ACTIVE");
    await new Promise((r) => setTimeout(r, 500));
  }
}

async function seedData() {
  await ddb.send(new PutCommand({
    TableName: TABLE,
    Item: {
      PK: "LINK#promo",
      SK: "META",
      enabled: true,
      destinationUrl: "https://example.com",
    },
  }));
}

(async () => {
  console.log(`[seed] Esperando endpoint ${ENDPOINT} ...`);
  await waitForDynamo();
  console.log("[seed] Asegurando tabla...");
  await ensureTable();
  console.log("[seed] Insertando datos...");
  await seedData();
  console.log("[seed] OK");
})().catch((e) => {
  console.error("[seed] ERROR:", e);
  process.exit(1);
});
