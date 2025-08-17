"""
API Upload - Manejo de carga de archivos
"""
import os
import logging
from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename
from hdfs import InsecureClient

from .utils import safe_json_response, format_error_response
from ..utils.validators import validate_file_upload

logger = logging.getLogger(__name__)
upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_data():
    """Cargar y analizar archivo CSV"""
    try:
        # Validar archivo
        validation_error = validate_file_upload(request)
        if validation_error:
            return safe_json_response(validation_error, 400)
        
        file = request.files['file']
        analytics = current_app.analytics
        config = current_app.config
        
        # Verificar que Spark esté disponible
        if not analytics.is_healthy():
            return safe_json_response({
                'error': 'Spark no está disponible',
                'message': 'El sistema está funcionando en modo limitado.'
            }, 503)
        
        # Preparar archivo
        filename = secure_filename(file.filename)
        local_path = os.path.join(config['UPLOAD_FOLDER'], filename)
        
        # Guardar temporalmente
        file.save(local_path)
        logger.info(f"Archivo guardado localmente: {local_path}")
        
        # Subir a HDFS
        hdfs_path = _upload_to_hdfs(local_path, filename, config)
        if not hdfs_path:
            return safe_json_response(
                format_error_response("Error subiendo archivo a HDFS"), 500
            )
        
        # Analizar con Spark
        spark_path = f"{config['HADOOP_NAMENODE_URL']}{hdfs_path}"
        analysis, error = analytics.load_dataset(spark_path)
        
        # Limpiar archivo temporal
        _cleanup_local_file(local_path)
        
        if error:
            return safe_json_response(format_error_response(error), 500)
        
        return safe_json_response({
            'message': 'Archivo cargado y analizado exitosamente',
            'filename': filename,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error en upload: {e}")
        return safe_json_response(
            format_error_response(f'Error procesando archivo: {str(e)}'), 500
        )

def _upload_to_hdfs(local_path: str, filename: str, config: dict) -> str:
    """Subir archivo a HDFS"""
    try:
        client = InsecureClient(config['HADOOP_NAMENODE_WEB_URL'], user=config['HDFS_USER'])
        hdfs_path = f'/user/hdfs/data/{filename}'
        
        # Crear directorio si no existe
        try:
            if not client.status('/user/hdfs/data', strict=False):
                client.makedirs('/user/hdfs/data')
        except:
            client.makedirs('/user/hdfs/data')
        
        # Subir archivo
        client.upload(hdfs_path, local_path, overwrite=True)
        logger.info(f"Archivo subido a HDFS: {hdfs_path}")
        return hdfs_path
        
    except Exception as e:
        logger.error(f"Error subiendo a HDFS: {e}")
        return None

def _cleanup_local_file(local_path: str):
    """Eliminar archivo temporal"""
    try:
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.debug(f"Archivo temporal eliminado: {local_path}")
    except Exception as e:
        logger.warning(f"Error eliminando archivo temporal: {e}")