from fastapi import APIRouter, status, Response, HTTPException
from app.models.link_schemas import LinkCreate, LinkOut # Asumiendo que estos modelos siguen bien
# --- CAMBIO EN IMPORTACIÓN ---
# Se quita get_item y se añade get_link_by_id
from app.services.link_service import (
    create_link,
    list_links,
    delete_link,
    get_link_by_id, # <-- El nombre nuevo
    get_link_metrics # <-- Importamos la función de métricas correcta
)
# -----------------------------

router = APIRouter(prefix="/links", tags=["Links"])


# --- CAMBIO: Usar async def ---
@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
async def create_link_endpoint(payload: LinkCreate):
    # --- CAMBIO: Usar await ---
    return await create_link(payload)


# --- CAMBIO: Usar async def ---
@router.get("")
async def list_links_endpoint():
    # --- CAMBIO: Usar await ---
    items = await list_links()
    return {"items": items}


# --- CAMBIO: Usar async def ---
@router.get("/{link_id}", response_model=LinkOut) # Definir un response_model es buena práctica
async def get_link_endpoint(link_id: str):
    # --- CAMBIO: Usar await y la función correcta ---
    # La función get_link_by_id ya maneja el 404 con HTTPException
    link = await get_link_by_id(link_id)
    return link


# --- CAMBIO: Usar async def ---
@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link_endpoint(link_id: str):
    # --- CAMBIO: Usar await ---
    # La función delete_link ya maneja el 404/500 con HTTPException
    await delete_link(link_id)
    # FastAPI devuelve 204 automáticamente si no retornas nada
    return Response(status_code=status.HTTP_204_NO_CONTENT) # Opcional, pero explícito


# --- CAMBIO: Usar async def ---
@router.get("/{link_id}/metrics")
async def get_metrics_endpoint(link_id: str):
    # --- CAMBIO: Usar await ---
    # La función get_link_metrics ya maneja errores con HTTPException
    metrics = await get_link_metrics(link_id)
    return metrics
