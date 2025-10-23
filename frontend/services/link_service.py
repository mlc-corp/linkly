# services/link_service.py
import os
import requests
from typing import Optional, List, Dict
import re


class LinkService:
    """Servicio para manejar la lógica de negocio de los links, consumiendo MS Admin API"""
    
    def __init__(self):
        """Inicializa el servicio con la URL del MS Admin"""
        self.admin_api_url = os.getenv('ADMIN_API_URL', 'http://localhost:3000')
        # Asegurar que la URL no termine con /
        self.admin_api_url = self.admin_api_url.rstrip('/')
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Realiza una petición HTTP al MS Admin
        
        Args:
            method: Método HTTP (GET, POST, DELETE, etc.)
            endpoint: Endpoint relativo (ej: /links)
            **kwargs: Argumentos adicionales para requests
        
        Returns:
            Response object
        
        Raises:
            requests.RequestException: Si hay error de conexión
        """
        url = f"{self.admin_api_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=10,  # 10 segundos de timeout
                **kwargs
            )
            return response
        except requests.RequestException as e:
            print(f"[LinkService] Error al conectar con MS Admin: {e}")
            raise
    
    def get_all_links(self) -> List[Dict]:
        """
        Obtiene todos los links desde MS Admin
        
        Returns:
            List[Dict]: Lista de links
        
        Raises:
            requests.RequestException: Si hay error de conexión
            ValueError: Si la respuesta es inválida
        """
        try:
            response = self._make_request('GET', '/links')
            
            if response.status_code == 200:
                data = response.json()
                return data.get('items', [])
            else:
                print(f"[LinkService] Error al obtener links: {response.status_code}")
                return []
                
        except requests.RequestException:
            raise
        except Exception as e:
            print(f"[LinkService] Error inesperado al obtener links: {e}")
            return []
    
    def get_link_by_id(self, link_id: str) -> Optional[Dict]:
        """
        Obtiene un link por su ID desde MS Admin
        
        Args:
            link_id: ID del link
        
        Returns:
            Dict con la información del link o None si no existe
        
        Raises:
            requests.RequestException: Si hay error de conexión
        """
        try:
            response = self._make_request('GET', f'/links/{link_id}')
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"[LinkService] Error al obtener link {link_id}: {response.status_code}")
                return None
                
        except requests.RequestException:
            raise
        except Exception as e:
            print(f"[LinkService] Error inesperado al obtener link: {e}")
            return None
    
    def create_link(self, title: str, slug: str, destination_url: str, variants: List[str]) -> Dict:
        """
        Crea un nuevo link en MS Admin
        
        Args:
            title: Título del link
            slug: URL corta
            destination_url: URL de destino
            variants: Lista de variantes
        
        Returns:
            Dict con el link creado
        
        Raises:
            ValueError: Si los datos son inválidos o el slug ya existe
            requests.RequestException: Si hay error de conexión
        """
        
        # Validaciones locales (antes de enviar al backend)
        if not title or not title.strip():
            raise ValueError('El título es requerido')
        
        if not slug or not slug.strip():
            raise ValueError('El slug es requerido')
        
        if not destination_url or not destination_url.strip():
            raise ValueError('La URL de destino es requerida')
        
        # Validar formato del slug
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError('El slug solo puede contener letras minúsculas, números y guiones')
        
        # Preparar el payload según el formato esperado por MS Admin
        payload = {
            'slug': slug.strip(),
            'title': title.strip(),
            'destinationUrl': destination_url.strip(),
            'variants': variants if variants else []
        }
        
        try:
            response = self._make_request(
                'POST',
                '/links',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                return response.json()
            elif response.status_code == 400:
                # Error de validación del backend
                error_data = response.json()
                error_message = error_data.get('error', 'Error de validación')
                raise ValueError(error_message)
            elif response.status_code == 409:
                # Conflicto - slug ya existe
                raise ValueError('El slug ya existe')
            else:
                print(f"[LinkService] Error al crear link: {response.status_code}")
                raise ValueError(f'Error del servidor: {response.status_code}')
                
        except requests.RequestException:
            raise
        except ValueError:
            raise
        except Exception as e:
            print(f"[LinkService] Error inesperado al crear link: {e}")
            raise ValueError('Error al crear el link')
    
    def delete_link(self, link_id: str) -> bool:
        """
        Elimina un link en MS Admin
        
        Args:
            link_id: ID del link a eliminar
        
        Returns:
            bool: True si se eliminó, False si no existe
        
        Raises:
            requests.RequestException: Si hay error de conexión
        """
        try:
            response = self._make_request('DELETE', f'/links/{link_id}')
            
            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                return False
            else:
                print(f"[LinkService] Error al eliminar link {link_id}: {response.status_code}")
                return False
                
        except requests.RequestException:
            raise
        except Exception as e:
            print(f"[LinkService] Error inesperado al eliminar link: {e}")
            return False
    
    def get_link_metrics(self, link_id: str) -> Optional[Dict]:
        """
        Obtiene las métricas de un link desde MS Admin
        
        Args:
            link_id: ID del link
        
        Returns:
            Dict con las métricas o None si el link no existe
        
        Raises:
            requests.RequestException: Si hay error de conexión
        """
        try:
            response = self._make_request('GET', f'/links/{link_id}/metrics')
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"[LinkService] Error al obtener métricas de {link_id}: {response.status_code}")
                return None
                
        except requests.RequestException:
            raise
        except Exception as e:
            print(f"[LinkService] Error inesperado al obtener métricas: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Verifica si MS Admin está disponible
        
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        try:
            response = self._make_request('GET', '/health')
            return response.status_code == 200 and response.json().get('ok') == True
        except:
            return False