# services/link_service.py
from datetime import datetime
import uuid
import re
import random


class LinkService:
    """Servicio para manejar la lógica de negocio de los links"""
    
    def __init__(self):
        """Inicializa el servicio con datos de prueba"""
        self.links_db = []
        self.metrics_db = {}
        self._inicializar_datos_prueba()
    
    def _generate_link_id(self):
        """Genera un ID único para el link"""
        return f"lk_{uuid.uuid4().hex[:12]}"
    
    def _inicializar_datos_prueba(self):
        """Inicializa datos de prueba para visualizar métricas"""
        
        # Link 1: Evento 2025 con muchos clics
        link1_id = "lk_demo001"
        link1 = {
            'linkId': link1_id,
            'title': 'Evento 2025',
            'slug': 'evento2025',
            'destinationUrl': 'https://myevent.com',
            'variants': ['default', 'ig', 'facebook', 'x', 'linkedin'],
            'createdAt': '2025-01-15T10:00:00Z'
        }
        self.links_db.append(link1)
        
        self.metrics_db[link1_id] = {
            'slug': 'evento2025',
            'totals': {
                'clicks': 3450,
                'byVariant': {
                    'default': 450,
                    'ig': 1200,
                    'facebook': 980,
                    'x': 520,
                    'linkedin': 300
                },
                'byDevice': {
                    'mobile': 2100,
                    'desktop': 1050,
                    'tablet': 300
                },
                'byCountry': {
                    'CO': 1500,
                    'US': 850,
                    'MX': 620,
                    'ES': 280,
                    'AR': 200
                }
            }
        }
        
        # Link 2: Promo Black Friday con clics moderados
        link2_id = "lk_demo002"
        link2 = {
            'linkId': link2_id,
            'title': 'Promo Black Friday',
            'slug': 'blackfriday2025',
            'destinationUrl': 'https://tienda.com/promo',
            'variants': ['default', 'ig', 'tiktok', 'whatsapp'],
            'createdAt': '2025-02-01T08:30:00Z'
        }
        self.links_db.append(link2)
        
        self.metrics_db[link2_id] = {
            'slug': 'blackfriday2025',
            'totals': {
                'clicks': 1820,
                'byVariant': {
                    'default': 220,
                    'ig': 750,
                    'tiktok': 580,
                    'whatsapp': 270
                },
                'byDevice': {
                    'mobile': 1450,
                    'desktop': 280,
                    'tablet': 90
                },
                'byCountry': {
                    'CO': 980,
                    'US': 420,
                    'MX': 320,
                    'PE': 100
                }
            }
        }
        
        # Link 3: Webinar con pocos clics
        link3_id = "lk_demo003"
        link3 = {
            'linkId': link3_id,
            'title': 'Webinar Gratuito',
            'slug': 'webinar-gratis',
            'destinationUrl': 'https://zoom.us/webinar123',
            'variants': ['default', 'email', 'linkedin'],
            'createdAt': '2025-03-10T14:00:00Z'
        }
        self.links_db.append(link3)
        
        self.metrics_db[link3_id] = {
            'slug': 'webinar-gratis',
            'totals': {
                'clicks': 420,
                'byVariant': {
                    'default': 80,
                    'email': 240,
                    'linkedin': 100
                },
                'byDevice': {
                    'mobile': 150,
                    'desktop': 250,
                    'tablet': 20
                },
                'byCountry': {
                    'CO': 180,
                    'US': 120,
                    'ES': 80,
                    'MX': 40
                }
            }
        }
        
        # Link 4: Link sin clics aún
        link4_id = "lk_demo004"
        link4 = {
            'linkId': link4_id,
            'title': 'Nuevo Producto',
            'slug': 'nuevo-producto',
            'destinationUrl': 'https://producto.com',
            'variants': ['default', 'ig', 'facebook'],
            'createdAt': '2025-10-22T18:00:00Z'
        }
        self.links_db.append(link4)
        
        self.metrics_db[link4_id] = {
            'slug': 'nuevo-producto',
            'totals': {
                'clicks': 0,
                'byVariant': {
                    'default': 0,
                    'ig': 0,
                    'facebook': 0
                },
                'byDevice': {},
                'byCountry': {}
            }
        }
    
    def get_all_links(self):
        """Obtiene todos los links"""
        return self.links_db
    
    def get_link_by_id(self, link_id):
        """Obtiene un link por su ID"""
        return next((l for l in self.links_db if l['linkId'] == link_id), None)
    
    def get_link_by_slug(self, slug):
        """Obtiene un link por su slug"""
        return next((l for l in self.links_db if l['slug'] == slug), None)
    
    def create_link(self, title, slug, destination_url, variants):
        """
        Crea un nuevo link
        
        Args:
            title: Título del link
            slug: URL corta
            destination_url: URL de destino
            variants: Lista de variantes
        
        Returns:
            dict: Link creado
        
        Raises:
            ValueError: Si los datos son inválidos
        """
        
        # Validaciones
        if not title or not slug or not destination_url:
            raise ValueError('Título, slug y URL de destino son requeridos')
        
        # Validar que el slug no exista
        if self.get_link_by_slug(slug):
            raise ValueError('El slug ya existe')
        
        # Validar formato del slug
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValueError('El slug solo puede contener letras minúsculas, números y guiones')
        
        # Asegurar que haya al menos la variante "default"
        if not variants:
            variants = ['default']
        elif 'default' not in variants:
            variants.insert(0, 'default')
        
        # Crear el link
        link_id = self._generate_link_id()
        new_link = {
            'linkId': link_id,
            'title': title,
            'slug': slug,
            'destinationUrl': destination_url,
            'variants': variants,
            'createdAt': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.links_db.append(new_link)
        
        # Inicializar métricas vacías
        self.metrics_db[link_id] = {
            'slug': slug,
            'totals': {
                'clicks': 0,
                'byVariant': {v: 0 for v in variants},
                'byDevice': {},
                'byCountry': {}
            }
        }
        
        return new_link
    
    def delete_link(self, link_id):
        """
        Elimina un link
        
        Args:
            link_id: ID del link a eliminar
        
        Returns:
            bool: True si se eliminó, False si no existe
        """
        link = self.get_link_by_id(link_id)
        
        if not link:
            return False
        
        # Eliminar link
        self.links_db = [l for l in self.links_db if l['linkId'] != link_id]
        
        # Eliminar métricas asociadas
        if link_id in self.metrics_db:
            del self.metrics_db[link_id]
        
        return True
    
    def get_link_metrics(self, link_id):
        """
        Obtiene las métricas de un link
        
        Args:
            link_id: ID del link
        
        Returns:
            dict: Métricas del link o None si no existe
        """
        link = self.get_link_by_id(link_id)
        
        if not link:
            return None
        
        # Obtener métricas o devolver vacías
        return self.metrics_db.get(link_id, {
            'slug': link['slug'],
            'totals': {
                'clicks': 0,
                'byVariant': {v: 0 for v in link['variants']},
                'byDevice': {},
                'byCountry': {}
            }
        })
    
    def simulate_metrics(self, link_id):
        """
        Simula métricas para un link (solo desarrollo)
        
        Args:
            link_id: ID del link
        
        Returns:
            dict: Métricas simuladas o None si no existe
        """
        link = self.get_link_by_id(link_id)
        
        if not link:
            return None
        
        # Inicializar métricas si no existen
        if link_id not in self.metrics_db:
            self.metrics_db[link_id] = {
                'slug': link['slug'],
                'totals': {
                    'clicks': 0,
                    'byVariant': {v: 0 for v in link['variants']},
                    'byDevice': {},
                    'byCountry': {}
                }
            }
        
        metrics = self.metrics_db[link_id]['totals']
        
        # Generar clics aleatorios por variante
        total_clicks = 0
        for variant in link['variants']:
            clicks = random.randint(50, 500)
            metrics['byVariant'][variant] = clicks
            total_clicks += clicks
        
        # Simular dispositivos
        metrics['byDevice'] = {
            'mobile': random.randint(100, 800),
            'desktop': random.randint(50, 400),
            'tablet': random.randint(10, 100)
        }
        
        # Simular países
        metrics['byCountry'] = {
            'CO': random.randint(200, 600),
            'US': random.randint(100, 400),
            'MX': random.randint(50, 300),
            'ES': random.randint(30, 200),
            'AR': random.randint(20, 150)
        }
        
        # Ajustar total de clics
        total_devices = sum(metrics['byDevice'].values())
        metrics['clicks'] = total_devices
        
        return self.metrics_db[link_id]
    
    def clear_all_data(self):
        """Limpia todos los datos (útil para testing)"""
        self.links_db = []
        self.metrics_db = {}