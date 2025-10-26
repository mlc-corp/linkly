import logging
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud.firestore_v1.client import Client
from google.cloud.firestore_v1.async_client import AsyncClient # Usar cliente asíncrono
from google.cloud.firestore_v1 import AsyncTransaction, transactional # Usar transacciones asíncronas
from google.cloud.firestore_v1.base_query import FieldFilter

# --- CORRECCIÓN IMPORTANTE ---
# from app.db.dynamo import get_db # <-- ESTABA MAL
from app.db.dynamo import get_db # <-- ASÍ ES CORRECTO
# -----------------------------

from app.core.config import settings # Asumiendo que settings tiene las colecciones

logger = logging.getLogger(__name__)

# Leer nombres de colecciones desde settings para consistencia
LINKS_COLLECTION = settings.LINKS_COLLECTION
SLUGS_COLLECTION = settings.SLUGS_COLLECTION
METRICS_COLLECTION = settings.METRICS_COLLECTION

# --- Funciones de Ayuda (Mantenidas o Adaptadas) ---

def gen_link_id() -> str:
    """Genera un ID único para los links."""
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
    return parts[1] if len(parts) == 2 and parts[1] else "default"

# --- Funciones Principales (Unificadas y Asíncronas) ---

async def get_link_by_id(link_id: str):
    """
    Obtiene un link desde Firestore por su linkId (documento en colección 'links').
    """
    db: AsyncClient = get_db() # Obtiene la instancia Async de Firestore
    logger.debug(f"Buscando link en Firestore con ID={link_id} en colección '{LINKS_COLLECTION}'")
    try:
        doc_ref = db.collection(LINKS_COLLECTION).document(link_id)
        doc = await doc_ref.get()

        if not doc.exists:
            logger.warning(f"Link no encontrado en Firestore para ID={link_id}")
            raise HTTPException(status_code=404, detail=f"Link {link_id} no encontrado")

        logger.debug(f"Link encontrado en Firestore para ID={link_id}")
        link_data = doc.to_dict()
        link_data['linkId'] = doc.id # Asegurarse que el ID esté presente
        return link_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado al buscar link {link_id} en Firestore: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Error inesperado al buscar el link en Firestore"
        )

# Usamos una transacción asíncrona explícita para mejor control con FastAPI
async def create_link(payload):
    """
    Crea un link y su slug asociado en Firestore usando una transacción asíncrona.
    """
    db: AsyncClient = get_db()
    transaction = db.transaction()

    # --- Validación de entrada (igual que antes) ---
    if not payload.title or not str(payload.title).strip():
        logger.warning("Intento de crear link con título vacío.")
        raise HTTPException(status_code=400, detail="El título es requerido")

    slug = payload.slug or payload.title.lower().strip().replace(" ", "-")
    # Añade validación más robusta de slug si es necesario
    if not slug:
        logger.warning(f"Intento de crear link con slug inválido: {slug}")
        raise HTTPException(status_code=400, detail="Slug inválido.")

    if not payload.destinationUrl or not str(payload.destinationUrl).strip():
        logger.warning("Intento de crear link con URL de destino vacía.")
        raise HTTPException(status_code=400, detail="La URL de destino es requerida")

    # --- Preparación de datos (igual que antes) ---
    link_id = gen_link_id()
    created_at = datetime.now(timezone.utc).isoformat()
    variants = (
        payload.variants
        if isinstance(payload.variants, list)
        else [v.strip() for v in (payload.variants or "").split(",") if v.strip()]
    )
    if "default" not in variants:
        variants.append("default")

    link_doc_data = {
        "linkId": link_id, # Redundante si el ID del doc es link_id, pero útil tenerlo dentro
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": list(set(variants)),
        "enabled": True,
        "createdAt": created_at,
        "updatedAt": created_at,
    }
    slug_doc_data = { "linkId": link_id } # Documento simple para mapeo

    logger.info(f"Intentando crear link en transacción: ID={link_id}, Slug={slug}")

    try:
        # Definir la lógica de la transacción
        @firestore.async_transactional # Decorador para manejar commit/rollback
        async def _run_create_transaction(transaction: AsyncTransaction):
            link_ref = db.collection(LINKS_COLLECTION).document(link_id)
            slug_ref = db.collection(SLUGS_COLLECTION).document(slug)

            # Verificar si el slug ya existe DENTRO de la transacción
            slug_doc = await transaction.get(slug_ref, field_paths=["linkId"])
            if slug_doc.exists:
                logger.warning(f"Colisión de slug detectada en transacción: {slug}")
                # Lanzar una excepción específica o devolver un estado
                raise AlreadyExists("El slug ya existe")

            # Si no existe, crear ambos documentos
            transaction.set(link_ref, link_doc_data)
            transaction.set(slug_ref, slug_doc_data)
            logger.info(f"Documentos preparados en transacción para linkId: {link_id}, Slug: {slug}")

        # Ejecutar la transacción
        await _run_create_transaction(transaction)

    except AlreadyExists as e_alias:
        # El decorador @async_transactional convierte AlreadyExists en un error HTTP si no se maneja
        raise HTTPException(status_code=409, detail=str(e_alias))
    except Exception as e:
        logger.error(
            f"Error Firestore inesperado al crear link {slug}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Error Firestore al crear link: {e}"
        )

    logger.info(f"Link creado exitosamente: ID={link_id}, Slug={slug}")
    return link_doc_data # Devolver el link creado

async def list_links():
    """ Lista todos los links (documentos principales) desde Firestore. """
    db: AsyncClient = get_db()
    logger.info(f"Listando todos los links desde '{LINKS_COLLECTION}'...")
    try:
        links_stream = db.collection(LINKS_COLLECTION).stream()
        items = []
        async for doc in links_stream:
            data = doc.to_dict()
            data['linkId'] = doc.id # Asegurar que el ID esté
            items.append(data)

        logger.info(f"Listado completado. Encontrados {len(items)} items.")
        # Opcional: formatear la salida si es necesario (ya lo hace tu código original)
        return items

    except Exception as e:
        logger.error(f"Error Firestore al listar links: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error Firestore al listar links: {e}"
        )

# Usamos transacción asíncrona explícita también para borrar
async def delete_link(link_id: str):
    """ Borra un link y su slug asociado usando una transacción asíncrona. """
    db: AsyncClient = get_db()
    transaction = db.transaction()
    logger.info(f"Intentando eliminar link en transacción con ID: {link_id}")

    try:
        @firestore.async_transactional
        async def _run_delete_transaction(transaction: AsyncTransaction):
            link_ref = db.collection(LINKS_COLLECTION).document(link_id)
            # Leer el link DENTRO de la transacción para obtener el slug
            link_doc = await transaction.get(link_ref)

            if not link_doc.exists:
                logger.warning(f"Intento de eliminar link no encontrado en transacción: {link_id}")
                raise NotFound("Link no encontrado")

            link_data = link_doc.to_dict()
            slug = link_data.get("slug")

            # Borrar el link principal
            transaction.delete(link_ref)
            logger.debug(f"Maestro preparado para eliminar en transacción: {link_id}")

            # Borrar el slug si existe
            if slug:
                slug_ref = db.collection(SLUGS_COLLECTION).document(slug)
                # Opcional: verificar si existe antes de borrar, aunque delete es idempotente
                transaction.delete(slug_ref)
                logger.debug(f"Slug preparado para eliminar en transacción: {slug}")
            else:
                 logger.warning(f"Link {link_id} no tenía slug asociado, no se borró slug.")

        # Ejecutar la transacción
        await _run_delete_transaction(transaction)

        logger.info(f"Eliminación completada exitosamente para linkId: {link_id}")
        # En FastAPI, un DELETE exitoso usualmente devuelve un 204 No Content (sin cuerpo)
        # o un mensaje simple. No necesitas devolver nada aquí si tu endpoint maneja el 204.

    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error inesperado durante la eliminación del link {link_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error inesperado al eliminar link: {e}"
        )


async def get_link_metrics(link_id: str):
    """
    Agrega métricas para un link_id dado desde Firestore.
    (Esta función ya estaba bien en el archivo original abierto, la copio aquí
     para unificar, asegurándome que use el cliente async y settings).
    """
    db: AsyncClient = get_db()
    logger.info(f"Calculando métricas agregadas de Firestore para linkId={link_id}")

    link = await get_link_by_id(link_id) # Llama a la versión unificada
    slug = link.get("slug")
    if not slug:
        logger.error(f"Link maestro {link_id} no tiene slug.")
        raise HTTPException(status_code=500, detail="Error interno: Link maestro sin slug.")

    declared_variants = link.get("variants") or ["default"]
    logger.debug(f"Consultando métricas en Firestore para slug={slug} en colección '{METRICS_COLLECTION}'...")

    try:
        start_at_id = f"{slug}#"
        end_at_id = f"{slug}#~"
        query = db.collection(METRICS_COLLECTION).where(filter=FieldFilter("__name__", ">=", start_at_id)).where(filter=FieldFilter("__name__", "<", end_at_id))

        docs_stream = query.stream()
        metric_items = []
        async for doc in docs_stream:
            item_data = doc.to_dict()
            item_data['doc_id'] = doc.id
            metric_items.append(item_data)
        logger.info(f"Consulta de métricas para slug={slug} encontró {len(metric_items)} items.")
    except Exception as e:
        logger.error(f"Error Firestore durante consulta de métricas para slug={slug}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error Firestore al consultar métricas")

    # --- Procesamiento (igual que antes) ---
    found_variants = {_variant_from_metric_id(i["doc_id"]) for i in metric_items}
    variants_to_process = sorted(list(found_variants)) if found_variants else list(declared_variants)
    logger.debug(f"Agregando métricas para las variantes: {variants_to_process}")
    by_variant_item_map = {_variant_from_metric_id(i["doc_id"]): i for i in metric_items}
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
            except (ValueError, TypeError): clicks = 0
            _sum_maps(aggregated_by_device, item.get("byDevice"))
            _sum_maps(aggregated_by_country, item.get("byCountry"))
        else: clicks = 0
        aggregated_by_variant[v] = clicks
        total_clicks += clicks

    # --- Respuesta (igual que antes) ---
    result = {
        "slug": slug, "linkId": link_id,
        "totals": {
            "clicks": total_clicks, "byVariant": aggregated_by_variant,
            "byDevice": aggregated_by_device, "byCountry": aggregated_by_country,
        },
    }
    logger.info(f"Métricas agregadas calculadas para linkId={link_id}")
    return result

