# app.py
from flask import Flask
from routes.web_routes import web_bp
from routes.api_routes import api_bp

def create_app():
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config['DEBUG'] = True
    
    # Registrar blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("🚀 Linkly Frontend - Iniciando")
    print("=" * 60)
    print("🌐 Abre: http://localhost:5000/app")
    print("=" * 60)
    
    app.run(debug=True, port=5000)