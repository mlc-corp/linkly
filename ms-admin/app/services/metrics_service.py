from app.db.dynamo import table
from botocore.exceptions import ClientError
from fastapi import HTTPException

def get_link_by_id(link_id: str):
    """
    Obtiene un link desde DynamoDB por su linkId.
    """
    try:
        resp = table.get_item(
            Key={"PK": f"LINK#{link_id}", "SK": "META"},
            ConsistentRead=True
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")

    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Link {link_id} not found")

    return item


def get_link_metrics(link_id: str):
    """
    Calcula las métricas totales de un link a partir de sus variantes,
    agregando clicks, dispositivos y países.
    """
    link = get_link_by_id(link_id)

    slug = link.get("slug")
    variants = link.get("variants") or ["default"]

    total_clicks = 0
    by_variant = {}
    by_device = {}
    by_country = {}

    for v in variants:
        pk = f"METRIC#{slug}#{v}"
        try:
            resp = table.get_item(Key={"PK": pk, "SK": "TOTAL"}, ConsistentRead=True)
        except ClientError:
            resp = {}

        item = resp.get("Item")
        clicks = 0

        if item:
            clicks = int(item.get("clicks", 0))
            # merge byDevice
            for d, n in (item.get("byDevice") or {}).items():
                by_device[d] = by_device.get(d, 0) + int(n)
            # merge byCountry
            for c, n in (item.get("byCountry") or {}).items():
                by_country[c] = by_country.get(c, 0) + int(n)

        by_variant[v] = clicks
        total_clicks += clicks

    return {
        "slug": slug,
        "totals": {
            "clicks": total_clicks,
            "byVariant": by_variant,
            "byDevice": by_device,
            "byCountry": by_country,
        },
    }
