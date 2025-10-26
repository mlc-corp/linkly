from datetime import datetime, timezone
import uuid
import logging
from fastapi import HTTPException
from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud.firestore_v1.client import Client
from google.cloud.firestore_v1 import Transaction, transactional

from app.db.firestore_client import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

LINKS_COLLECTION = settings.LINKS_COLLECTION
SLUGS_COLLECTION = settings.SLUGS_COLLECTION

def gen_link_id() -> str:
    return f"lk_{uuid.uuid4().hex[:8]}"

def _get_link_by_id(link_id: str):
    db: Client = get_db()
    logger.debug(f"Obteniendo link con ID={link_id}")
    try:
        doc_ref = db.collection(LINKS_COLLECTION).document(link_id)
        doc = doc_ref.get()
        if doc.exists:
            logger.debug(f"Item encontrado para ID={link_id}")
            return doc.to_dict()
        else:
            logger.warning(f"Item NO encontrado para ID={link_id}")
            return None
    except Exception as e:
        logger.error(
            f"Error Firestore al obtener item ID={link_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error Firestore al buscar item: {e}",
        )

@transactional
def _create_link_transaction(
    transaction: Transaction, link_doc_data: dict, slug_doc_data: dict
):
    db: Client = get_db()
    link_id = link_doc_data["linkId"]
    slug = link_doc_data["slug"]

    link_ref = db.collection(LINKS_COLLECTION).document(link_id)
    slug_ref = db.collection(SLUGS_COLLECTION).document(slug)

    slug_doc = transaction.get(slug_ref, field_to_return=["linkId"])
    if slug_doc.exists:
        logger.warning(f"Colisión de slug detectada: {slug}")
        raise AlreadyExists("El slug ya existe")

    transaction.set(link_ref, link_doc_data)
    transaction.set(slug_ref, slug_doc_data)
    logger.info(f"Transacción completada para linkId: {link_id}, Slug: {slug}")


def create_link(payload):
    db: Client = get_db()

    if not payload.title or not str(payload.title).strip():
        logger.warning("Intento de crear link con título vacío.")
        raise HTTPException(status_code=400, detail="El título es requerido")

    slug = payload.slug or payload.title.lower().strip().replace(" ", "-")
    if not slug:
        logger.warning(f"Intento de crear link con slug inválido: {slug}")
        raise HTTPException(
            status_code=400, detail="Slug inválido."
        )

    if not payload.destinationUrl or not str(payload.destinationUrl).strip():
        logger.warning("Intento de crear link con URL de destino vacía.")
        raise HTTPException(status_code=400, detail="La URL de destino es requerida")

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
        "linkId": link_id,
        "slug": slug,
        "title": payload.title.strip(),
        "destinationUrl": str(payload.destinationUrl),
        "variants": list(set(variants)),
        "enabled": True,
        "createdAt": created_at,
        "updatedAt": created_at,
    }

    slug_doc_data = {
        "linkId": link_id,
    }

    logger.info(f"Intentando crear link: ID={link_id}, Slug={slug}")

    try:
        transaction = db.transaction()
        _create_link_transaction(transaction, link_doc_data, slug_doc_data)

    except AlreadyExists as e_alias:
        raise HTTPException(status_code=409, detail=str(e_alias))
    except Exception as e:
        logger.error(
            f"Error Firestore inesperado al crear link {slug}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error Firestore: {e}"
        )

    logger.info(f"Link creado exitosamente: ID={link_id}, Slug={slug}")
    return link_doc_data


def list_links():
    db: Client = get_db()
    logger.info("Listando todos los links...")
    try:
        docs = db.collection(LINKS_COLLECTION).stream()
        items = [doc.to_dict() for doc in docs]
        
        logger.info(f"Listado completado. Encontrados {len(items)} items.")

        result = [
            {
                "linkId": i.get("linkId"),
                "slug": i.get("slug"),
                "title": i.get("title"),
                "destinationUrl": i.get("destinationUrl"),
                "variants": i.get("variants"),
                "createdAt": i.get("createdAt"),
                "enabled": i.get("enabled", True),
            }
            for i in items
            if i.get("linkId")
        ]
        return result

    except Exception as e:
        logger.error(f"Error Firestore al listar links: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error Firestore al listar: {e}",
        )

@transactional
def _delete_link_transaction(transaction: Transaction, link_id: str):
    db: Client = get_db()
    
    link_ref = db.collection(LINKS_COLLECTION).document(link_id)
    link_doc = transaction.get(link_ref)
    
    if not link_doc.exists:
        logger.warning(f"Intento de eliminar link no encontrado: {link_id}")
        raise NotFound("Link no encontrado")

    link_data = link_doc.to_dict()
    slug = link_data.get("slug")

    transaction.delete(link_ref)
    logger.debug(f"Maestro eliminado en transacción: {link_id}")

    if slug:
        slug_ref = db.collection(SLUGS_COLLECTION).document(slug)
        transaction.delete(slug_ref)
        logger.debug(f"Slug/alias eliminado en transacción: {slug}")
    
    return slug

def delete_link(link_id: str):
    db: Client = get_db()
    logger.info(f"Intentando eliminar link con ID: {link_id}")

    try:
        transaction = db.transaction()
        _delete_link_transaction(transaction, link_id)
        
        logger.info(
            f"Eliminación completada para linkId: {link_id}."
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error inesperado durante la eliminación del link {link_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error inesperado al eliminar: {e}"
        )
