from fastapi import APIRouter, status, Response
from app.models.link_schemas import LinkCreate, LinkOut
from app.services.link_service import create_link, list_links, delete_link, get_item
from app.services.metrics_service import get_link_metrics

router = APIRouter(prefix="/links", tags=["Links"])


@router.post("", response_model=LinkOut, status_code=status.HTTP_201_CREATED)
def create_link_endpoint(payload: LinkCreate):
    return create_link(payload)


@router.get("")
def list_links_endpoint():
    return {"items": list_links()}


@router.get("/{link_id}")
def get_link_endpoint(link_id: str):
    item = get_item(f"LINK#{link_id}", "META")
    if not item:
        return Response(status_code=404)
    return item


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link_endpoint(link_id: str):
    delete_link(link_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{link_id}/metrics")
def get_metrics_endpoint(link_id: str):
    return get_link_metrics(link_id)
