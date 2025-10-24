# routes/web_routes.py
import os
from flask import Blueprint, render_template, redirect, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

web_bp = Blueprint("web", __name__)

# Cargar el dominio base desde .env
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "linkly.space")


@web_bp.route("/")
def index():
    """Redirecciona a la aplicación principal"""
    return redirect(url_for("web.app_home"))


@web_bp.route("/app")
def app_home():
    """Renderiza la página principal con lista de links"""
    return render_template("index.html", base_domain=BASE_DOMAIN)


@web_bp.route("/app/links/<link_id>")
def link_detail(link_id):
    """Renderiza la página de detalle de un link"""
    return render_template("detail.html", link_id=link_id, base_domain=BASE_DOMAIN)


@web_bp.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"ok": True}), 200
