"""
API Health - Endpoints de salud del sistema
"""
import logging
from flask import Blueprint, current_app
from .utils import safe_json_response

logger = logging.getLogger(__name__)
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Verificar estado del sistema"""
    try:
        analytics = current_app.analytics
        status = analytics.get_system_status()
        
        # Verificar HDFS (simplificado)
        hadoop_status = 'ok'  # Aquí podrías agregar verificación real de HDFS
        status['hadoop'] = hadoop_status
        
        return safe_json_response(status)
        
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return safe_json_response({
            'flask': 'error',
            'spark': 'error',
            'hadoop': 'error',
            'error': str(e)
        }, 503)