# routes/api_routes.py
from flask import Blueprint, request, jsonify
from services.link_service import LinkService
import requests


ERROR_SERVER = "Error interno del servidor"
ERROR_LINK_NOT_FOUND = "Link no encontrado"
ERROR_NO_DATA = "No se enviaron datos"
ERROR_CONNECTION = (
    "No se pudo conectar con el servidor. Verifica que MS Admin esté ejecutándose."
)


api_bp = Blueprint("api", __name__)
link_service = LinkService()


def handle_connection_error():
    """Maneja errores de conexión con MS Admin"""
    return jsonify({"error": ERROR_CONNECTION}), 503


@api_bp.route("/links", methods=["GET"])
def get_links():
    """Obtiene todos los links"""
    try:
        links = link_service.get_all_links()
        return jsonify({"items": links}), 200
    except requests.RequestException:
        return handle_connection_error()
    except Exception as e:
        print(f"[API] Error al obtener links: {e}")
        return jsonify({"error": ERROR_SERVER}), 500


@api_bp.route("/links", methods=["POST"])
def create_link():
    """Crea un nuevo link"""
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": ERROR_NO_DATA}), 400

        new_link = link_service.create_link(
            title=data.get("title", "").strip(),
            slug=data.get("slug", "").strip(),
            destination_url=data.get("destinationUrl", "").strip(),
            variants=data.get("variants", []),
        )

        return jsonify(new_link), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except requests.RequestException:
        return handle_connection_error()
    except Exception as e:
        print(f"[API] Error al crear link: {e}")
        return jsonify({"error": ERROR_SERVER}), 500


@api_bp.route("/links/<link_id>", methods=["GET"])
def get_link(link_id):
    """Obtiene los detalles de un link específico"""
    try:
        link = link_service.get_link_by_id(link_id)

        if not link:
            return jsonify({"error": ERROR_LINK_NOT_FOUND}), 404

        return jsonify(link), 200

    except requests.RequestException:
        return handle_connection_error()
    except Exception as e:
        print(f"[API] Error al obtener link {link_id}: {e}")
        return jsonify({"error": ERROR_SERVER}), 500


@api_bp.route("/links/<link_id>", methods=["DELETE"])
def delete_link(link_id):
    """Elimina un link del sistema"""
    try:
        success = link_service.delete_link(link_id)

        if not success:
            return jsonify({"error": ERROR_LINK_NOT_FOUND}), 404

        return "", 204

    except requests.RequestException:
        return handle_connection_error()
    except Exception as e:
        print(f"[API] Error al eliminar link {link_id}: {e}")
        return jsonify({"error": ERROR_SERVER}), 500


@api_bp.route("/links/<link_id>/metrics", methods=["GET"])
def get_link_metrics(link_id):
    """Obtiene las métricas de un link"""
    try:
        metrics = link_service.get_link_metrics(link_id)

        if not metrics:
            return jsonify({"error": ERROR_LINK_NOT_FOUND}), 404

        return jsonify(metrics), 200

    except requests.RequestException:
        return handle_connection_error()
    except Exception as e:
        print(f"[API] Error al obtener métricas de {link_id}: {e}")
        return jsonify({"error": ERROR_SERVER}), 500


@api_bp.route("/health", methods=["GET"])
def health():
    """Health check del frontend y MS Admin"""
    try:
        admin_healthy = link_service.health_check()

        return (
            jsonify(
                {
                    "ok": True,
                    "frontend": "healthy",
                    "msAdmin": "healthy" if admin_healthy else "unhealthy",
                }
            ),
            200,
        )

    except Exception as e:
        print(f"[API] Error en health check: {e}")
        return (
            jsonify(
                {
                    "ok": False,
                    "frontend": "healthy",
                    "msAdmin": "unhealthy",
                    "error": str(e),
                }
            ),
            503,
        )
