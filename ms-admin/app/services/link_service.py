from datetime import datetime, timezone
import uuid
import logging  # Usar logging
from botocore.exceptions import ClientError
from fastapi import HTTPException

# --- CAMBIO EN IMPORTACIÓN ---
# Ya no importamos 'table' directamente
# from app.db.dynamo import table
from app.db.dynamo import get_table  # Importamos la función

# -----------------------------

logger = logging.getLogger(__name__)


def gen_link_id() -> str:
    """Genera un ID único para los links."""
    return f"lk_{uuid.uuid4().hex[:8]}"


def get_item(pk: str, sk: str):
    """Obtiene un item específico de DynamoDB por su PK y SK."""
    table = get_table()  # Obtiene la tabla al ser necesitada
    logger.debug(f"Obteniendo item con PK={pk}, SK={sk}")
    try:
        resp = table.get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True)
        item = resp.get("Item")
        if item:
            logger.debug(f"Item encontrado para PK={pk}, SK={sk}")
        else:
            logger.warning(f"Item NO encontrado para PK={pk}, SK={sk}")
        return item
    except ClientError as e:
        logger.error(
            f"Error DynamoDB al obtener item PK={pk}, SK={sk}: {e}", exc_info=True
        )
        # Propaga un error HTTP 500 para errores inesperados de DB
        raise HTTPException(
            status_code=500,
            detail=f"Error DynamoDB al buscar item: {e.response['Error']['Code']}",
        )


def delete_item(pk: str, sk: str):
    """Elimina un item específico de DynamoDB."""
    table = get_table()  # Obtiene la tabla
    logger.info(f"Eliminando item con PK={pk}, SK={sk}")
    try:
        response = table.delete_item(Key={"PK": pk, "SK": sk})
        logger.debug(f"Resultado de delete_item para PK={pk}, SK={sk}: {response}")
        return response  # Devuelve la respuesta de DynamoDB
    except ClientError as e:
        logger.error(
            f"Error DynamoDB al eliminar item PK={pk}, SK={sk}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error DynamoDB al eliminar item: {e.response['Error']['Code']}",
        )


def create_link(payload):
    """
    Crea 2 ítems: maestro por ID y alias por slug.
    Maneja colisiones de slug revirtiendo la creación.
    """
    table = get_table()  # Obtiene la tabla

    # --- Validación de entrada ---
    if not payload.title or not str(payload.title).strip():
        logger.warning("Intento de crear link con título vacío.")
        raise HTTPException(status_code=400, detail="El título es requerido")

    # Genera slug si no se proporciona (asegúrate que esto sea seguro para URLs)
    # Considera una librería para generar slugs seguros si payload.title puede tener caracteres especiales
    slug = payload.slug or payload.title.lower().strip().replace(" ", "-")
    # Añade validación de caracteres permitidos en el slug si es necesario
    if (
        not slug or not slug.isalnum() and "-" not in slug
    ):  # Ejemplo básico de validación
        logger.warning(f"Intento de crear link con slug inválido: {slug}")
        raise HTTPException(
            status_code=400, detail="Slug inválido, solo alfanuméricos y guiones."
        )

    link_id = gen_link_id()
    created_at = datetime.now(timezone.utc).isoformat()
    # Asegura que variants sea una lista, incluso si viene vacío o nulo
    variants = (
        payload.variants
        if isinstance(payload.variants, list)
        else [v.strip() for v in (payload.variants or "").split(",") if v.strip()]
    )
    if "default" not in variants:
        variants.append("default")  # Asegura que 'default' siempre exista

    if not payload.destinationUrl or not str(payload.destinationUrl).strip():
        logger.warning("Intento de crear link con URL de destino vacía.")
        raise HTTPException(status_code=400, detail="La URL de destino es requerida")

    # --- Creación de Items ---
    meta_item = {
        "PK": f"LINK#{link_id}",
        "SK": "META",  # Usar SK específico para el item principal
        "linkId": link_id,
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": list(set(variants)),  # Elimina duplicados
        "enabled": True,
        "createdAt": created_at,
        "updatedAt": created_at,  # Añadir updatedAt
    }

    alias_item = {
        "PK": f"LINK#{slug}",  # PK basado en slug para búsqueda rápida
        "SK": "ALIAS",  # Usar SK específico para alias
        "linkId": link_id,  # Apunta al ID del item principal
        # No necesitas duplicar toda la data aquí, solo lo esencial para ms-redirect
        # "slug": slug,
        # "destinationUrl": str(payload.destinationUrl),
        # "variants": list(set(variants)),
        # "enabled": True,
        # "createdAt": created_at,
    }

    logger.info(f"Intentando crear link: ID={link_id}, Slug={slug}")

    # --- Lógica Transaccional Simulada ---
    try:
        # 1) Intenta crear el alias por slug (este es el que puede colisionar)
        logger.debug(
            f"Intentando crear alias: PK={alias_item['PK']}, SK={alias_item['SK']}"
        )
        table.put_item(
            Item=alias_item,
            ConditionExpression="attribute_not_exists(PK)",  # Falla si el slug ya existe
        )
        logger.info(f"Alias creado exitosamente para slug: {slug}")

        # 2) Si el alias se creó, intenta crear el maestro por ID
        try:
            logger.debug(
                f"Intentando crear maestro: PK={meta_item['PK']}, SK={meta_item['SK']}"
            )
            table.put_item(
                Item=meta_item,
                ConditionExpression="attribute_not_exists(PK)",  # Debería funcionar siempre (ID único)
            )
            logger.info(f"Maestro creado exitosamente para linkId: {link_id}")

        except ClientError as e_meta:
            # Si falla el maestro (muy raro), hay que borrar el alias creado
            logger.error(
                f"Error al crear maestro para linkId {link_id} después de crear alias. Revirtiendo alias...",
                exc_info=True,
            )
            try:
                delete_item(alias_item["PK"], alias_item["SK"])  # Revertir alias
                logger.warning(f"Alias revertido para slug: {slug}")
            except Exception:
                logger.critical(
                    f"¡FALLO AL REVERTIR ALIAS para slug {slug} después de fallo en maestro! Estado inconsistente.",
                    exc_info=True,
                )
            # Propaga el error original del maestro
            raise HTTPException(
                status_code=500,
                detail=f"Error DynamoDB (maestro): {e_meta.response['Error']['Code']}",
            )

    except ClientError as e_alias:
        # Si falla el alias (lo más común es colisión)
        code = e_alias.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            logger.warning(f"Colisión de slug detectada: {slug}")
            raise HTTPException(status_code=409, detail="El slug ya existe")
        else:
            # Otro error al crear el alias
            logger.error(
                f"Error DynamoDB inesperado al crear alias para slug {slug}: {e_alias}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Error DynamoDB (alias): {code}"
            )

    # Si todo fue bien, devolvemos el item maestro creado
    logger.info(f"Link creado exitosamente: ID={link_id}, Slug={slug}")
    return meta_item


def list_links():
    """
    Lista todos los links maestros (items principales).
    """
    table = get_table()  # Obtiene la tabla
    logger.info("Listando todos los links (scan)...")
    try:
        # Scan es costoso. Considera GSI si necesitas filtrar eficientemente.
        # Filtra por SK='META' si es posible, o hazlo en la aplicación.
        resp = table.scan(
            FilterExpression="SK = :sk_val",  # Filtra solo los items maestros
            ExpressionAttributeValues={":sk_val": "META"},
        )
        items = resp.get("Items", [])
        logger.info(f"Scan completado. Encontrados {len(items)} items maestros.")

        # Formatea la salida si es necesario (puede que no necesites todos los campos)
        result = [
            {
                "linkId": i.get("linkId"),
                "slug": i.get("slug"),
                "title": i.get("title"),
                "destinationUrl": i.get("destinationUrl"),
                "variants": i.get("variants"),
                "createdAt": i.get("createdAt"),
                "enabled": i.get("enabled", True),  # Devuelve True si no existe
            }
            for i in items
            if i.get("linkId")  # Asegura que el item tenga linkId
        ]
        return result

    except ClientError as e:
        logger.error(f"Error DynamoDB al listar links (scan): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error DynamoDB al listar: {e.response['Error']['Code']}",
        )


def delete_link(link_id: str):
    """
    Borra el maestro por ID y su alias por slug correspondiente.
    """
    logger.info(f"Intentando eliminar link con ID: {link_id}")

    # 1. Obtener el item maestro para saber el slug
    item = get_item(f"LINK#{link_id}", "META")  # Usa la función get_item refactorizada
    if not item:
        logger.warning(f"Intento de eliminar link no encontrado: {link_id}")
        raise HTTPException(status_code=404, detail="Link no encontrado")

    slug = item.get("slug")
    if not slug:
        # Esto no debería pasar si create_link funciona bien, pero es bueno manejarlo
        logger.error(
            f"Link maestro {link_id} encontrado pero no tiene slug. No se puede borrar alias."
        )
        # Decide si continuar borrando solo el maestro o fallar
        # Por ahora, borraremos solo el maestro

    # 2. Intentar borrar ambos items (maestro y alias)
    deleted_count = 0
    try:
        # Borrar maestro
        logger.debug(f"Eliminando maestro: PK=LINK#{link_id}, SK=META")
        delete_item(
            f"LINK#{link_id}", "META"
        )  # Usa la función delete_item refactorizada
        deleted_count += 1
        logger.info(f"Maestro eliminado para linkId: {link_id}")

        # Borrar alias si existe slug
        if slug:
            logger.debug(f"Eliminando alias: PK=LINK#{slug}, SK=ALIAS")
            # Podrías verificar si el alias existe antes, pero delete es idempotente
            delete_item(
                f"LINK#{slug}", "ALIAS"
            )  # Usa la función delete_item refactorizada
            deleted_count += 1
            logger.info(f"Alias eliminado para slug: {slug}")

        logger.info(
            f"Eliminación completada para linkId: {link_id}. Items borrados: {deleted_count}"
        )
        # No retornamos nada en un DELETE exitoso (HTTP 204)

    except HTTPException as http_exc:
        # Si get_item o delete_item lanzaron HTTPException (ej: 500), propágala
        raise http_exc
    except Exception as e:
        # Captura cualquier otro error inesperado durante el proceso
        logger.error(
            f"Error inesperado durante la eliminación del link {link_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Error inesperado al eliminar el link"
        )
