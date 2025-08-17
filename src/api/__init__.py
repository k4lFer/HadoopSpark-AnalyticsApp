
"""
API Blueprints - Registro modular de rutas
"""
from flask import render_template

from .health import health_bp
from .upload import upload_bp
from .query import query_bp
from .data import data_bp

def register_blueprints(app):
    """Registrar todos los blueprints"""
    
    # Ruta principal
    @app.route('/')
    def index():
        return render_template('dashboard.html')
    
    # Registrar blueprints de API
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(upload_bp, url_prefix='/api')
    app.register_blueprint(query_bp, url_prefix='/api')
    app.register_blueprint(data_bp, url_prefix='/api')