from datetime import datetime, timezone
import uuid
import logging # Usar logging
from botocore.exceptions import ClientError
from fastapi import HTTPException
# --- CAMBIO EN IMPORTACIÓN ---
# Ya no importamos 'table' directamente
# from app.db.dynamo import table 
from app.db.dynamo import get_table # Importamos la función
# -----------------------------

logger = logging.getLogger(__name__)

def gen_link_id() -> str:
    """Genera un ID único para los links."""
    return f"lk_{uuid.uuid4().hex[:8]}"

def get_item(pk: str, sk: str):
    """Obtiene un item específico de DynamoDB por su PK y SK."""
    table = get_table() # Obtiene la tabla al ser necesitada
    logger.debug(f"Obteniendo item con PK={pk}, SK={sk}")
    try:
        resp = table.get_item(Key={"PK": pk, "SK": sk}, ConsistentRead=True)
        item = resp.get("Item")
        if item:
            logger.debug(f"Item encontrado para PK={pk}, SK={sk}")
        else:
            # En get_item, es normal no encontrar, no loguear como warning a menos que sea inesperado
            logger.debug(f"Item NO encontrado para PK={pk}, SK={sk}") 
        return item
    except ClientError as e:
        logger.error(f"Error DynamoDB al obtener item PK={pk}, SK={sk}: {e}", exc_info=True)
        # Propaga un error HTTP 500 para errores inesperados de DB
        raise HTTPException(status_code=500, detail=f"Error DynamoDB al buscar item: {e.response['Error']['Code']}")

def delete_item(pk: str, sk: str):
    """Elimina un item específico de DynamoDB."""
    table = get_table() # Obtiene la tabla
    logger.info(f"Eliminando item con PK={pk}, SK={sk}")
    try:
        response = table.delete_item(Key={"PK": pk, "SK": sk})
        logger.debug(f"Resultado de delete_item para PK={pk}, SK={sk}: {response}")
        return response # Devuelve la respuesta de DynamoDB
    except ClientError as e:
        logger.error(f"Error DynamoDB al eliminar item PK={pk}, SK={sk}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error DynamoDB al eliminar item: {e.response['Error']['Code']}")


def create_link(payload):
    """
    Crea 2 ítems: maestro por ID y alias por slug.
    Maneja colisiones de slug revirtiendo la creación.
    """
    # --- Validación de entrada PRIMERO ---
    if not payload.title or not str(payload.title).strip():
        logger.warning("Intento de crear link con título vacío.")
        raise HTTPException(status_code=400, detail="El título es requerido")
    
    slug = payload.slug or payload.title.lower().strip().replace(" ", "-") 
    if not slug: # Slug no puede ser vacío después de procesar
        logger.warning("Intento de crear link con slug vacío.")
        raise HTTPException(status_code=400, detail="El slug es requerido")
    # Añade validación de caracteres si es necesario
    # Ejemplo: if not re.match(r"^[a-zA-Z0-9-]+$", slug): raise HTTPException(...)

    if not payload.destinationUrl or not str(payload.destinationUrl).strip():
         logger.warning("Intento de crear link con URL de destino vacía.")
         raise HTTPException(status_code=400, detail="La URL de destino es requerida")
         
    # --- Obtener la tabla DESPUÉS de la validación ---
    table = get_table() 
    # ----------------------------------------------------

    link_id = gen_link_id()
    created_at = datetime.now(timezone.utc).isoformat()
    # Asegura que variants sea una lista, incluso si viene vacío o nulo
    variants = payload.variants if isinstance(payload.variants, list) else [v.strip() for v in (payload.variants or "").split(',') if v.strip()]
    if "default" not in variants:
         variants.append("default") 
    
    # --- Creación de Items ---
    meta_item = {
        "PK": f"LINK#{link_id}", "SK": "META", 
        "linkId": link_id, "slug": slug, "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl), "variants": list(set(variants)), 
        "enabled": True, "createdAt": created_at, "updatedAt": created_at,
    }
    alias_item = {
        "PK": f"LINK#{slug}", "SK": "ALIAS", "linkId": link_id,
        # Considera añadir otros campos si ms-redirect los necesita directamente
    }

    logger.info(f"Intentando crear link: ID={link_id}, Slug={slug}")
    
    # --- Lógica Transaccional Simulada ---
    master_created = False
    try:
        # 1) Intenta crear el alias por slug (este es el que puede colisionar)
        logger.debug(f"Intentando crear alias: PK={alias_item['PK']}, SK={alias_item['SK']}")
        table.put_item(
            Item=alias_item, 
            ConditionExpression="attribute_not_exists(PK)" 
        )
        logger.info(f"Alias creado exitosamente para slug: {slug}")

        # 2) Si el alias se creó, intenta crear el maestro por ID
        try:
            logger.debug(f"Intentando crear maestro: PK={meta_item['PK']}, SK={meta_item['SK']}")
            table.put_item(
                Item=meta_item, 
                ConditionExpression="attribute_not_exists(PK)" 
            )
            master_created = True
            logger.info(f"Maestro creado exitosamente para linkId: {link_id}")

        except ClientError as e_meta:
             logger.error(f"Error al crear maestro para linkId {link_id} después de crear alias. Revirtiendo alias...", exc_info=True)
             try:
                 # Usa la función helper para revertir, maneja errores
                 delete_item(alias_item["PK"], alias_item["SK"]) 
                 logger.warning(f"Alias revertido para slug: {slug}")
             except Exception as e_revert_alias:
                 logger.critical(f"¡FALLO AL REVERTIR ALIAS para slug {slug} después de fallo en maestro! Estado inconsistente.", exc_info=True)
             # Propaga el error original del maestro como 500
             raise HTTPException(status_code=500, detail=f"Error DynamoDB (maestro): {e_meta.response['Error']['Code']}")

    except ClientError as e_alias:
        # Si falla el alias (lo más común es colisión)
        code = e_alias.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            logger.warning(f"Colisión de slug detectada: {slug}")
            raise HTTPException(status_code=409, detail="El slug ya existe")
        else:
            logger.error(f"Error DynamoDB inesperado al crear alias para slug {slug}: {e_alias}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error DynamoDB (alias): {code}")
    except HTTPException: # Si delete_item falló al revertir y lanzó HTTPException
        raise
    except Exception as e: # Captura cualquier otro error inesperado
        logger.error(f"Error inesperado en create_link para slug {slug}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error inesperado al crear el link")
        
    logger.info(f"Link creado exitosamente: ID={link_id}, Slug={slug}")
    return meta_item


def list_links():
    """
    Lista todos los links maestros (items principales).
    """
    table = get_table() # Obtiene la tabla
    logger.info("Listando todos los links (scan)...")
    try:
        # Filtra directamente en DynamoDB si es posible
        resp = table.scan(
            FilterExpression="SK = :sk_val", 
            ExpressionAttributeValues={":sk_val": "META"} 
        )
        items = resp.get("Items", [])
        # Considerar paginación aquí si la tabla puede crecer mucho
        logger.info(f"Scan completado. Encontrados {len(items)} items maestros.")
        
        # Formatea la salida
        result = [
            {
                "linkId": i.get("linkId"), "slug": i.get("slug"), "title": i.get("title"),
                "destinationUrl": i.get("destinationUrl"), "variants": i.get("variants"),
                "createdAt": i.get("createdAt"), "enabled": i.get("enabled", True), 
            } for i in items if i.get("linkId") and i.get("PK") == f"LINK#{i.get('linkId')}" # Doble check por si acaso
        ]
        return result

    except ClientError as e:
        logger.error(f"Error DynamoDB al listar links (scan): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error DynamoDB al listar: {e.response['Error']['Code']}")
    except Exception as e:
        logger.error(f"Error inesperado al listar links: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error inesperado al listar links")


def delete_link(link_id: str):
    """
    Borra el maestro por ID y su alias por slug correspondiente.
    """
    logger.info(f"Intentando eliminar link con ID: {link_id}")

    # 1. Obtener el item maestro para saber el slug
    # get_item ya maneja el 404 y errores 500
    item = get_item(f"LINK#{link_id}", "META") 
    if not item: 
         # Esto no debería alcanzarse si get_item lanza 404, pero por seguridad
         raise HTTPException(status_code=404, detail="Link no encontrado") 

    slug = item.get("slug")
    if not slug:
         logger.error(f"Link maestro {link_id} encontrado pero no tiene slug. No se puede borrar alias.")
         # Decide si fallar o continuar
         raise HTTPException(status_code=500, detail="Error interno: Link maestro sin slug.")

    # 2. Intentar borrar ambos items (maestro y alias)
    deleted_count = 0
    errors = []
    try:
        # Borrar maestro (usa la función helper que ya maneja errores)
        logger.debug(f"Eliminando maestro: PK=LINK#{link_id}, SK=META")
        delete_item(f"LINK#{link_id}", "META") 
        deleted_count += 1
        logger.info(f"Maestro eliminado para linkId: {link_id}")
        
    except HTTPException as e:
        logger.error(f"Error al eliminar maestro para linkId {link_id}: {e.detail}")
        errors.append(f"maestro ({e.status_code})")
    except Exception as e:
         logger.error(f"Error inesperado al eliminar maestro para linkId {link_id}", exc_info=True)
         errors.append("maestro (inesperado)")

    # Intenta borrar alias incluso si falló el maestro (para limpiar)
    try:
        logger.debug(f"Eliminando alias: PK=LINK#{slug}, SK=ALIAS")
        delete_item(f"LINK#{slug}", "ALIAS") 
        deleted_count += 1
        logger.info(f"Alias eliminado para slug: {slug}")
    except HTTPException as e:
        # No lanza 404 si el alias no existía, delete_item debería manejarlo o necesitar ajuste
        if e.status_code != 404: # Ignora 404 para el alias (puede no existir)
             logger.error(f"Error al eliminar alias para slug {slug}: {e.detail}")
             errors.append(f"alias ({e.status_code})")
    except Exception as e:
         logger.error(f"Error inesperado al eliminar alias para slug {slug}", exc_info=True)
         errors.append("alias (inesperado)")

    # Si hubo algún error, lanza una excepción 500
    if errors:
        raise HTTPException(status_code=500, detail=f"Errores durante la eliminación: {', '.join(errors)}")

    logger.info(f"Eliminación completada para linkId: {link_id}. Items borrados: {deleted_count}")
    # No se retorna nada en DELETE exitoso (FastAPI maneja 204)

