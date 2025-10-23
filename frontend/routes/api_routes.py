# routes/api_routes.py
from flask import Blueprint, request, jsonify
from services.link_service import LinkService

api_bp = Blueprint('api', __name__)
link_service = LinkService()


@api_bp.route('/links', methods=['GET'])
def get_links():
    """Obtiene todos los links"""
    try:
        links = link_service.get_all_links()
        return jsonify({'items': links}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/links', methods=['POST'])
def create_link():
    """Crea un nuevo link"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data:
            return jsonify({'error': 'No se enviaron datos'}), 400
        
        # Crear link usando el servicio
        new_link = link_service.create_link(
            title=data.get('title', '').strip(),
            slug=data.get('slug', '').strip(),
            destination_url=data.get('destinationUrl', '').strip(),
            variants=data.get('variants', [])
        )
        
        return jsonify(new_link), 201
        
    except ValueError as e:
        # Errores de validación
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/links/<link_id>', methods=['GET'])
def get_link(link_id):
    """Obtiene los detalles de un link específico"""
    try:
        link = link_service.get_link_by_id(link_id)
        
        if not link:
            return jsonify({'error': 'Link no encontrado'}), 404
        
        return jsonify(link), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/links/<link_id>', methods=['DELETE'])
def delete_link(link_id):
    """Elimina un link del sistema"""
    try:
        success = link_service.delete_link(link_id)
        
        if not success:
            return jsonify({'error': 'Link no encontrado'}), 404
        
        return '', 204
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/links/<link_id>/metrics', methods=['GET'])
def get_link_metrics(link_id):
    """Obtiene las métricas de un link"""
    try:
        metrics = link_service.get_link_metrics(link_id)
        
        if not metrics:
            return jsonify({'error': 'Link no encontrado'}), 404
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/links/<link_id>/metrics/simulate', methods=['POST'])
def simulate_clicks(link_id):
    """Endpoint para simular clics (solo para desarrollo/pruebas)"""
    try:
        metrics = link_service.simulate_metrics(link_id)
        
        if not metrics:
            return jsonify({'error': 'Link no encontrado'}), 404
        
        return jsonify({
            'message': 'Métricas simuladas exitosamente',
            'metrics': metrics
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500