import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
  DynamoDBDocumentClient,
  GetCommand,
  UpdateCommand,
} from "@aws-sdk/lib-dynamodb";

const REGION = process.env.AWS_REGION || "us-east-1";
const DDB_TABLE = process.env.DDB_TABLE;
const DDB_ENDPOINT = process.env.DDB_ENDPOINT;

if (!DDB_TABLE) {
  console.error("[ms-redirect] Falta DDB_TABLE en el .env");
  process.exit(1);
}

const baseClient = new DynamoDBClient({
  region: REGION,
  ...(DDB_ENDPOINT ? { endpoint: DDB_ENDPOINT } : {}),
  credentials:
    process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY
      ? {
          accessKeyId: process.env.AWS_ACCESS_KEY_ID,
          secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        }
      : undefined,
});

export const ddb = DynamoDBDocumentClient.from(baseClient, {
  marshallOptions: { removeUndefinedValues: true },
});

export async function getLinkBySlug(slug) {
  const { Item } = await ddb.send(
    new GetCommand({
      TableName: DDB_TABLE,
      Key: { PK: `LINK#${slug}`, SK: "META" },
      ConsistentRead: true,
    }),
  );

  if (!Item || Item.enabled === false) return null;
  return { destinationUrl: Item.destinationUrl };
}

export async function incrementMetrics({
  slug,
  variant = "default",
  country = "UN",
  device = "unknown",
}) {
  const c = (country || "UN").toUpperCase();
  const d = device || "unknown";

  await ddb.send(
    new UpdateCommand({
      TableName: DDB_TABLE,
      Key: { PK: `METRIC#${slug}#${variant}`, SK: "TOTAL" },
      UpdateExpression: [
        "SET byCountry = if_not_exists(byCountry, :empty)",
        "    , byDevice = if_not_exists(byDevice, :empty)",
        "    , byCountry.#c = if_not_exists(byCountry.#c, :zero) + :one",
        "    , byDevice.#d  = if_not_exists(byDevice.#d,  :zero) + :one",
        "ADD clicks :one",
      ].join(" "),
      ExpressionAttributeNames: { "#c": c, "#d": d },
      ExpressionAttributeValues: { ":one": 1, ":zero": 0, ":empty": {} },
      ReturnValues: "NONE",
    }),
  );
}
