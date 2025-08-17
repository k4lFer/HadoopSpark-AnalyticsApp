"""
Analytics API - Aplicación principal modular
"""
import os
import sys
import logging
from flask import Flask
from flask_cors import CORS


from config import Config
from src.core.analytics_app import AnalyticsApp
from src.api import register_blueprints
from src.utils.exceptions import handle_errors

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configurar CORS
    CORS(app)
    
    # Inicializar sistema analytics
    analytics_app = AnalyticsApp(config_class)
    app.analytics = analytics_app
    
    # Registrar blueprints (rutas modulares)
    register_blueprints(app)
    
    # Registrar manejadores de errores
    handle_errors(app)
    
    return app

def main():
    """Función principal"""
    # Crear directorios necesarios
    os.makedirs('/app/data', exist_ok=True)
    
    # Crear aplicación
    app = create_app()
    
    # Log de inicio
    logger.info("🚀 Iniciando Analytics API modular...")
    
    if app.analytics.is_healthy():
        logger.info("✅ Sistema completamente inicializado")
        cluster_info = app.analytics.get_cluster_info()
        if cluster_info:
            logger.info(f"🔧 Cluster Spark: {cluster_info}")
    else:
        logger.warning("⚠️ Sistema iniciado en modo limitado")
    
    # Ejecutar Flask
    logger.info("🌐 Servidor disponible en http://0.0.0.0:5000")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

if __name__ == '__main__':
    main()