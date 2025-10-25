import logging  # Usar logging
from botocore.exceptions import ClientError
from fastapi import HTTPException

# --- CAMBIO EN IMPORTACIÓN ---
# Ya no importamos 'table' directamente
# from app.db.dynamo import table
from app.db.dynamo import get_table  # Importamos la función

# -----------------------------

logger = logging.getLogger(__name__)


def _sum_maps(dst: dict, src: dict | None):
    """Suma los valores de src en dst (acumulador)."""
    if src is None:
        return
    for k, v in src.items():
        try:
            # Asegura que v sea numérico antes de sumar
            dst[k] = dst.get(k, 0) + int(v)
        except (ValueError, TypeError):
            # Ignora valores no numéricos en los mapas de métricas
            logger.warning(
                f"Valor no numérico '{v}' encontrado en mapa de métricas para clave '{k}'. Ignorando."
            )
            pass


def _variant_from_pk(pk: str) -> str:
    """Extrae la variante del PK de métrica (ej: METRIC#slug#variant)."""
    parts = pk.split("#", 2)
    # Devuelve 'default' si no hay parte de variante (o si el formato es inesperado)
    return parts[2] if len(parts) == 3 and parts[2] else "default"


def get_link_by_id(link_id: str):
    """
    Obtiene un link desde DynamoDB por su linkId (registro maestro).
    Reutiliza la lógica de obtener item si existe en otro módulo, o la define aquí.
    """
    table = get_table()  # Obtiene la tabla al ser necesitada
    logger.debug(f"Buscando link maestro con linkId={link_id}")
    try:
        resp = table.get_item(
            Key={"PK": f"LINK#{link_id}", "SK": "META"},  # Asume SK='META' para maestro
            ConsistentRead=True,
        )
        item = resp.get("Item")
        if not item:
            logger.warning(f"Link maestro no encontrado para linkId={link_id}")
            raise HTTPException(status_code=404, detail=f"Link {link_id} no encontrado")

        logger.debug(f"Link maestro encontrado para linkId={link_id}")
        return item  # Devuelve el item completo

    except ClientError as e:
        logger.error(
            f"Error DynamoDB al buscar link maestro {link_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error DynamoDB al buscar link: {e.response['Error']['Code']}",
        )
    except HTTPException:
        raise  # Propaga el 404 si get_item ya lo lanzó
    except Exception as e:
        logger.error(
            f"Error inesperado al buscar link maestro {link_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error inesperado al buscar el link"
        )


def get_link_metrics(link_id: str):
    """
    Agrega métricas para un link_id dado.
    """
    table = get_table()  # Obtiene la tabla
    logger.info(f"Calculando métricas agregadas para linkId={link_id}")

    # 1. Obtener el link maestro para saber el slug y las variantes declaradas
    #    Esta función ahora maneja el 404 internamente.
    link = get_link_by_id(link_id)
    slug = link.get("slug")
    if not slug:
        # Esto sería un error grave de datos si el item maestro no tiene slug
        logger.error(
            f"Link maestro {link_id} no tiene slug. No se pueden calcular métricas."
        )
        raise HTTPException(
            status_code=500, detail="Error interno: Link maestro sin slug."
        )

    declared_variants = link.get("variants") or ["default"]

    # 2. Descubrir variantes existentes con métricas usando Scan
    #    Scan puede ser ineficiente. Si tienes muchas variantes/links, considera un GSI.
    logger.debug(f"Escaneando métricas para slug={slug}...")
    try:
        scan_kwargs = {
            "FilterExpression": "begins_with(PK, :p) AND SK = :s",
            "ExpressionAttributeValues": {":p": f"METRIC#{slug}#", ":s": "TOTAL"},
            "ProjectionExpression": "PK, clicks, byDevice, byCountry",  # Solo trae los datos necesarios
            "ConsistentRead": True,  # O False si la consistencia eventual es aceptable
        }
        metric_items = []
        # Manejar paginación si la tabla es grande
        while True:
            resp = table.scan(**scan_kwargs)
            metric_items.extend(resp.get("Items", []))
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
            logger.debug("Paginando scan de métricas...")

        logger.info(
            f"Scan de métricas para slug={slug} encontró {len(metric_items)} items."
        )

    except ClientError as e:
        logger.error(
            f"Error DynamoDB durante scan de métricas para slug={slug}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error DynamoDB al escanear métricas: {e.response['Error']['Code']}",
        )

    # 3. Procesar y agregar las métricas encontradas
    found_variants = {_variant_from_pk(i["PK"]) for i in metric_items}

    # Usa las variantes encontradas; si no hay ninguna, usa las declaradas como fallback
    variants_to_process = (
        sorted(list(found_variants)) if found_variants else list(declared_variants)
    )
    logger.debug(f"Agregando métricas para las variantes: {variants_to_process}")

    # Indexa los items encontrados por variante para acceso rápido
    by_variant_item_map = {_variant_from_pk(i["PK"]): i for i in metric_items}

    # Inicializa los acumuladores
    total_clicks = 0
    aggregated_by_variant = {}
    aggregated_by_device = {}
    aggregated_by_country = {}

    for v in variants_to_process:
        item = by_variant_item_map.get(v)

        # Aunque el scan debería traer todo, agregamos un fallback por si acaso (ej. consistencia eventual)
        if item is None and v in found_variants:
            logger.warning(
                f"Variante '{v}' encontrada en scan pero no en el mapa. Intentando GetItem como fallback."
            )
            try:
                resp = table.get_item(
                    Key={"PK": f"METRIC#{slug}#{v}", "SK": "TOTAL"},
                    ConsistentRead=True,  # O False
                )
                item = resp.get("Item")
            except ClientError as e_get:
                logger.error(
                    f"Error en GetItem fallback para métrica {slug}/{v}: {e_get}",
                    exc_info=True,
                )
                item = None  # Trata como si no existiera si hay error

        # Procesa el item si existe
        clicks = 0
        if item:
            try:
                # Asegura que 'clicks' sea un número, default a 0 si no existe o es inválido
                clicks = int(item.get("clicks", 0))
            except (ValueError, TypeError):
                logger.warning(
                    f"Valor 'clicks' no numérico encontrado para métrica {slug}/{v}. Usando 0."
                )
                clicks = 0

            # Acumula los mapas
            _sum_maps(aggregated_by_device, item.get("byDevice"))
            _sum_maps(aggregated_by_country, item.get("byCountry"))
        else:
            logger.debug(
                f"No se encontraron datos de métricas para la variante '{v}'. Usando 0 clicks."
            )
            clicks = 0  # Asegura que clicks sea 0 si no hay item

        aggregated_by_variant[v] = clicks
        total_clicks += clicks

    # 4. Construir y devolver la respuesta final
    result = {
        "slug": slug,
        "linkId": link_id,  # Devuelve también el linkId
        "totals": {
            "clicks": total_clicks,
            "byVariant": aggregated_by_variant,
            "byDevice": aggregated_by_device,
            "byCountry": aggregated_by_country,
        },
        # Podrías añadir detalles por variante si fuera necesario
        # "detailsByVariant": by_variant_item_map
    }
    logger.info(f"Métricas agregadas calculadas para linkId={link_id}")
    return result
