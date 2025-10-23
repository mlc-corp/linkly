from datetime import datetime
import uuid
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.db.dynamo import table, dynamodb  # dynamodb por si luego quieres transacciones

def gen_link_id() -> str:
    return f"lk_{uuid.uuid4().hex[:8]}"

def get_item(pk: str, sk: str):
    resp = table.get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True)
    return resp.get("Item")

def delete_item(pk: str, sk: str):
    return table.delete_item(Key={"PK": pk, "SK": sk})

def create_link(payload):
    """
    Crea 2 ítems:
      - Maestro por ID:   PK=LINK#<linkId>, SK=META
      - Alias por slug:   PK=LINK#<slug>,   SK=META  (el que usa ms-redirect)
    Si el alias colisiona (slug ya existe), se revierte la creación del maestro.
    """
    if not payload.title or not str(payload.title).strip():
        raise HTTPException(status_code=400, detail="title es requerido")

    slug = payload.slug or payload.title.lower().strip().replace(" ", "-")
    link_id = gen_link_id()
    created_at = datetime.utcnow().isoformat() + "Z"

    # normaliza variants
    variants = payload.variants or ["default"]

    meta_item = {
        "PK": f"LINK#{link_id}",
        "SK": "META",
        "linkId": link_id,
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": variants,
        "enabled": True,
        "createdAt": created_at,
    }

    alias_item = {
        "PK": f"LINK#{slug}",
        "SK": "META",
        "linkId": link_id,
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": variants,
        "enabled": True,
        "createdAt": created_at,
    }

    try:
        # 1) Crea maestro por ID (si no existe)
        table.put_item(
            Item=meta_item,
            ConditionExpression="attribute_not_exists(PK)"
        )
        try:
            # 2) Crea alias por slug (si no existe)
            table.put_item(
                Item=alias_item,
                ConditionExpression="attribute_not_exists(PK)"
            )
        except ClientError as e_alias:
            # Si el alias ya existe, revertimos el maestro
            code = e_alias.response.get("Error", {}).get("Code")
            if code == "ConditionalCheckFailedException":
                delete_item(meta_item["PK"], meta_item["SK"])
                raise HTTPException(status_code=409, detail="El slug ya existe")
            # Otro error: revertimos y propagamos
            delete_item(meta_item["PK"], meta_item["SK"])
            raise HTTPException(status_code=500, detail=f"DynamoDB error (alias): {e_alias}")
    except ClientError as e_meta:
        raise HTTPException(status_code=500, detail=f"DynamoDB error (meta): {e_meta}")

    # Devolvemos la representación canónica (por ID)
    return meta_item

def list_links():
    """
    Lista únicamente los registros maestros (por ID) para evitar duplicados por alias.
    Criterio: SK = META y PK == f"LINK#{linkId}"
    """
    resp = table.scan()
    items = resp.get("Items", [])
    result = []
    for i in items:
        if i.get("SK") != "META":
            continue
        link_id = i.get("linkId")
        pk = i.get("PK")
        # Solo el maestro por ID (evita duplicar alias por slug)
        if not link_id or not pk or pk != f"LINK#{link_id}":
            continue
        result.append({
            "linkId": link_id,
            "slug": i.get("slug"),
            "title": i.get("title"),
            "destinationUrl": i.get("destinationUrl"),
            "variants": i.get("variants"),
            "createdAt": i.get("createdAt"),
            "enabled": i.get("enabled", True),
        })
    return result

def delete_link(linkId: str):
    """
    Borra el maestro por ID y, si existe, el alias por slug.
    """
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
