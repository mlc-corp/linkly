import logging
from fastapi import HTTPException
from datetime import datetime, timezone  # Mantener para timestamps si es necesario
import uuid # Mantener para gen_link_id si se usa aquí

# --- CAMBIO EN IMPORTACIÓN ---
# from app.db.dynamo import get_table
from app.db.dynamo import get_db # ¡Importamos el cliente de Firestore!
from google.cloud.firestore_v1.base_query import FieldFilter # Para filtros

# -----------------------------

# Asumiendo que estas variables vienen de tu config o settings
# Si no, defínelas aquí o pásalas a las funciones
# LINKS_COLLECTION = "links" # Colección principal de links (document ID = link_id)
# SLUGS_COLLECTION = "slugs" # Colección para mapeo slug -> link_id
# METRICS_COLLECTION = "metrics" # Colección para métricas (document ID = slug#variant)

logger = logging.getLogger(__name__)

# --- Funciones de Ayuda (Adaptadas o Mantenidas) ---

def gen_link_id() -> str:
    """Genera un ID único para los links."""
    # Esta función no depende de la DB, se mantiene igual
    return f"lk_{uuid.uuid4().hex[:8]}"

def _sum_maps(dst: dict, src: dict | None):
    """Suma los valores de src en dst (acumulador). Se mantiene igual."""
    if src is None:
        return
    for k, v in src.items():
        try:
            dst[k] = dst.get(k, 0) + int(v)
        except (ValueError, TypeError):
            logger.warning(
                f"Valor no numérico '{v}' encontrado en mapa de métricas para clave '{k}'. Ignorando."
            )
            pass

def _variant_from_metric_id(doc_id: str) -> str:
    """Extrae la variante del ID de documento de métrica (ej: slug#variant)."""
    parts = doc_id.split("#", 1)
    # Devuelve 'default' si no hay parte de variante
    return parts[1] if len(parts) == 2 and parts[1] else "default"

# --- Funciones Principales (Migradas a Firestore) ---

async def get_link_by_id(link_id: str, db=None): # Pasar db como argumento es buena práctica
    """
    Obtiene un link desde Firestore por su linkId (documento en colección 'links').
    """
    if not db:
        db = get_db() # Obtiene la instancia de Firestore si no se pasa

    # Asume que LINKS_COLLECTION está definida globalmente o en settings
    links_collection_name = "links" # O leer de settings/env
    logger.debug(f"Buscando link en Firestore con ID={link_id} en colección '{links_collection_name}'")

    try:
        doc_ref = db.collection(links_collection_name).document(link_id)
        doc = await doc_ref.get() # Usar await si es async

        if not doc.exists:
            logger.warning(f"Link no encontrado en Firestore para ID={link_id}")
            raise HTTPException(status_code=404, detail=f"Link {link_id} no encontrado")

        logger.debug(f"Link encontrado en Firestore para ID={link_id}")
        # Firestore devuelve un diccionario directamente
        link_data = doc.to_dict()
        link_data['linkId'] = doc.id # Añadir el ID al diccionario si no está
        return link_data

    except HTTPException:
        raise # Propaga el 404
    except Exception as e:
        logger.error(
            f"Error inesperado al buscar link {link_id} en Firestore: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error inesperado al buscar el link en Firestore"
        )

async def get_link_metrics(link_id: str, db=None):
    """
    Agrega métricas para un link_id dado desde Firestore.
    """
    if not db:
        db = get_db()

    logger.info(f"Calculando métricas agregadas de Firestore para linkId={link_id}")

    # 1. Obtener el link maestro para saber el slug y las variantes declaradas
    link = await get_link_by_id(link_id, db) # Reutiliza la función async
    slug = link.get("slug")
    if not slug:
        logger.error(
            f"Link maestro {link_id} no tiene slug. No se pueden calcular métricas."
        )
        raise HTTPException(
            status_code=500, detail="Error interno: Link maestro sin slug."
        )

    declared_variants = link.get("variants") or ["default"]

    # 2. Consultar métricas para ese slug en la colección de métricas
    #    En Firestore, hacemos una consulta con 'startswith' simulado
    metrics_collection_name = "metrics" # O leer de settings/env
    logger.debug(f"Consultando métricas en Firestore para slug={slug} en colección '{metrics_collection_name}'...")

    try:
        # Firestore no tiene 'startswith' directo en ID.
        # Necesitamos consultar por un campo 'slug' o usar un rango en el ID.
        # Opción A: Asumiendo que los documentos de métricas tienen un campo 'slug'
        # query = db.collection(metrics_collection_name).where(filter=FieldFilter("slug", "==", slug))

        # Opción B: Usando rango en el ID del documento (si el ID es slug#variant)
        # Necesita que los IDs estén bien formateados.
        start_at_id = f"{slug}#"
        end_at_id = f"{slug}#~" # Caracter mayor que '#' para simular startswith
        query = db.collection(metrics_collection_name).where(filter=FieldFilter("__name__", ">=", start_at_id)).where(filter=FieldFilter("__name__", "<", end_at_id))

        # Ejecutar la consulta de forma asíncrona
        docs_stream = query.stream()
        metric_items = []
        async for doc in docs_stream:
            item_data = doc.to_dict()
            item_data['doc_id'] = doc.id # Guardamos el ID para extraer variante
            metric_items.append(item_data)

        logger.info(
            f"Consulta de métricas para slug={slug} encontró {len(metric_items)} items."
        )

    except Exception as e:
        logger.error(
            f"Error Firestore durante consulta de métricas para slug={slug}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error Firestore al consultar métricas",
        )

    # 3. Procesar y agregar las métricas encontradas (similar a antes)
    found_variants = {_variant_from_metric_id(i["doc_id"]) for i in metric_items}
    variants_to_process = (
        sorted(list(found_variants)) if found_variants else list(declared_variants)
    )
    logger.debug(f"Agregando métricas para las variantes: {variants_to_process}")

    # Indexa los items encontrados por variante
    by_variant_item_map = {_variant_from_metric_id(i["doc_id"]): i for i in metric_items}

    # Inicializa acumuladores
    total_clicks = 0
    aggregated_by_variant = {}
    aggregated_by_device = {}
    aggregated_by_country = {}

    for v in variants_to_process:
        item = by_variant_item_map.get(v)
        clicks = 0
        if item:
            try:
                clicks = int(item.get("clicks", 0))
            except (ValueError, TypeError):
                logger.warning(
                    f"Valor 'clicks' no numérico encontrado para métrica {slug}/{v}. Usando 0."
                )
                clicks = 0
            _sum_maps(aggregated_by_device, item.get("byDevice"))
            _sum_maps(aggregated_by_country, item.get("byCountry"))
        else:
            logger.debug(
                f"No se encontraron datos de métricas para la variante '{v}'. Usando 0 clicks."
            )
            clicks = 0

        aggregated_by_variant[v] = clicks
        total_clicks += clicks

    # 4. Construir y devolver la respuesta final
    result = {
        "slug": slug,
        "linkId": link_id,
        "totals": {
            "clicks": total_clicks,
            "byVariant": aggregated_by_variant,
            "byDevice": aggregated_by_device,
            "byCountry": aggregated_by_country,
        },
    }
    logger.info(f"Métricas agregadas calculadas para linkId={link_id}")
    return result

# --- Nota: Funciones create_link, list_links, delete_link, get_item ---
# Estas funciones NO están en el código que me pasaste, pero si existen en
# tu 'link_service.py' original, también tendrías que migrarlas a Firestore.
# Por ejemplo, 'list_links' cambiaría de un 'scan' a un 'db.collection("links").stream()'.
# 'create_link' usaría una transacción de Firestore para crear el link y el slug.
# 'delete_link' usaría una transacción para borrar ambos documentos.
# 'get_item' sería reemplazado por llamadas directas a Firestore como en 'get_link_by_id'.
