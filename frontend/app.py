# app.py
import os
from flask import Flask
from routes.web_routes import web_bp
from routes.api_routes import api_bp
from dotenv import load_dotenv


def create_app():
    """Factory pattern para crear la aplicación Flask"""
    app = Flask(__name__)

    # Registrar blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


if __name__ == '__main__':
    # Cargar variables de entorno desde .env
    load_dotenv()

    app = create_app()

    # Obtener variables del entorno con valores por defecto
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("🚀 Linkly Frontend - Iniciando")
    print("=" * 60)
    print(f"🌐 Abre: http://localhost:{port}/app")
    print("=" * 60)

    app.run(debug=debug, port=port)
