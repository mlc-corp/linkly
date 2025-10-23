from datetime import datetime
import uuid
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.db.dynamo import table

def gen_link_id() -> str:
    return f"lk_{uuid.uuid4().hex[:8]}"

def get_item(pk: str, sk: str):
    resp = table.get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True)
    return resp.get("Item")

def delete_item(pk: str, sk: str):
    return table.delete_item(Key={"PK": pk, "SK": sk})

def create_link(payload):
    slug = payload.slug or payload.title.lower().replace(" ", "-")
    link_id = gen_link_id()
    created_at = datetime.utcnow().isoformat() + "Z"

    item = {
        "PK": f"LINK#{link_id}",
        "SK": "META",
        "linkId": link_id,
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": payload.variants,
        "createdAt": created_at,
    }

    try:
        table.put_item(Item=item)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")

    return item

def list_links():
    resp = table.scan()
    items = resp.get("Items", [])
    return [
        {
            "linkId": i["linkId"],
            "slug": i.get("slug"),
            "title": i.get("title"),
            "destinationUrl": i.get("destinationUrl"),
            "variants": i.get("variants"),
            "createdAt": i.get("createdAt"),
        }
        for i in items if i.get("SK") == "META" and "linkId" in i
    ]

def delete_link(linkId: str):
    item = get_item(f"LINK#{linkId}", "META")
    if not item:
        raise HTTPException(status_code=404, detail="Link not found")
    slug = item.get("slug")
    try:
        delete_item(f"LINK#{linkId}", "META")
        if slug:
            delete_item(f"LINK#{slug}", "META")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")
