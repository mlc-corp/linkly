from app.db.dynamo import table
from botocore.exceptions import ClientError
from fastapi import HTTPException

def _sum_maps(dst: dict, src: dict | None):
    for k, v in (src or {}).items():
        dst[k] = dst.get(k, 0) + int(v)

def _variant_from_pk(pk: str) -> str:
    # PK = "METRIC#<slug>#<variant>"
    parts = pk.split("#", 2)
    return parts[2] if len(parts) == 3 else "default"

def get_link_by_id(link_id: str):
    """
    Obtiene un link desde DynamoDB por su linkId (registro maestro).
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
    Agrega métricas por slug:
      - totals.clicks (suma de todas las variantes)
      - totals.byVariant  (clicks por variante)
      - totals.byDevice   (acumulado de mapas por variante)
      - totals.byCountry  (acumulado de mapas por variante)
    Descubre variantes presentes en Dynamo (PK = METRIC#<slug>#<variant>).
    """
    link = get_link_by_id(link_id)
    slug = link.get("slug")
    declared_variants = link.get("variants") or ["default"]

    # 1) Descubrir variantes existentes con métricas
    try:
        scan = table.scan(
            FilterExpression="begins_with(PK, :p) AND SK = :s",
            ExpressionAttributeValues={":p": f"METRIC#{slug}#", ":s": "TOTAL"},
            ProjectionExpression="PK,clicks,byDevice,byCountry",
            ConsistentRead=True,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {e}")

    items = scan.get("Items", []) or []
    found_variants = {_variant_from_pk(i["PK"]) for i in items}
    # Si no hay métricas aún, usa variantes declaradas como fallback
    variants = sorted(found_variants) if found_variants else list(declared_variants)

    # Index para acceso O(1) por variante
    by_variant_item = { _variant_from_pk(i["PK"]): i for i in items }

    total_clicks = 0
    by_variant = {}
    by_device = {}
    by_country = {}

    for v in variants:
        item = by_variant_item.get(v)
        if item is None:
            # Fallback por si no salió en el scan pero existe
            try:
                resp = table.get_item(
                    Key={"PK": f"METRIC#{slug}#{v}", "SK": "TOTAL"},
                    ConsistentRead=True
                )
                item = resp.get("Item")
            except ClientError:
                item = None

        clicks = int(item.get("clicks", 0)) if item else 0
        by_variant[v] = clicks
        total_clicks += clicks

        if item:
            _sum_maps(by_device, item.get("byDevice"))
            _sum_maps(by_country, item.get("byCountry"))

    return {
        "slug": slug,
        "totals": {
            "clicks": total_clicks,
            "byVariant": by_variant,   # p.ej. {"default": 2, "ig": 1}
            "byDevice": by_device,     # p.ej. {"mobile": 2, "desktop": 1}
            "byCountry": by_country,   # p.ej. {"CO": 2, "UN": 1}
        },
    }
