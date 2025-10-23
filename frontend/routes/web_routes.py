# routes/web_routes.py
from flask import Blueprint, render_template, redirect, url_for, jsonify

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Redirecciona a la aplicación principal"""
    return redirect(url_for('web.app_home'))


@web_bp.route('/app')
def app_home():
    """Renderiza la página principal con lista de links"""
    return render_template('index.html')


@web_bp.route('/app/links/<link_id>')
def link_detail(link_id):
    """Renderiza la página de detalle de un link"""
    return render_template('detail.html', link_id=link_id)


@web_bp.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'ok': True}), 200