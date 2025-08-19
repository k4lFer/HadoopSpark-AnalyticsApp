"""
Manejo de excepciones y errores personalizados
"""
import logging
from flask import Flask
from .responses import safe_json_response  # ✅ Import correcto desde el mismo paquete

logger = logging.getLogger(__name__)

class AnalyticsError(Exception):
    """Excepción base para errores de analytics"""
    pass

class SparkError(AnalyticsError):
    """Error relacionado con Spark"""
    pass

class DataError(AnalyticsError):
    """Error relacionado con datos"""
    pass

class ValidationError(AnalyticsError):
    """Error de validación"""
    pass

class HDFSError(AnalyticsError):
    """Error relacionado con HDFS"""
    pass

def handle_errors(app: Flask):
    """Registrar manejadores de errores globales"""
    
    @app.errorhandler(404)
    def not_found(error):
        """Manejo de error 404"""
        return safe_json_response({
            'error': 'Endpoint no encontrado',
            'message': 'La ruta solicitada no existe'
        }, 404)
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Manejo de error 405"""
        return safe_json_response({
            'error': 'Método no permitido',
            'message': 'El método HTTP no está permitido para esta ruta'
        }, 405)
    
    @app.errorhandler(413)
    def file_too_large(error):
        """Manejo de archivo muy grande"""
        return safe_json_response({
            'error': 'Archivo demasiado grande',
            'message': 'El archivo excede el tamaño máximo permitido (100MB)'
        }, 413)
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejo de error interno del servidor"""
        logger.error(f"Error interno del servidor: {error}")
        return safe_json_response({
            'error': 'Error interno del servidor',
            'message': 'Ocurrió un error inesperado'
        }, 500)
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Manejo de errores de validación"""
        logger.warning(f"Error de validación: {error}")
        return safe_json_response({
            'error': 'Error de validación',
            'message': str(error)
        }, 400)
    
    @app.errorhandler(SparkError)
    def handle_spark_error(error):
        """Manejo de errores de Spark"""
        logger.error(f"Error de Spark: {error}")
        return safe_json_response({
            'error': 'Error en Spark',
            'message': 'Error procesando datos con Spark'
        }, 503)
    
    @app.errorhandler(DataError)
    def handle_data_error(error):
        """Manejo de errores de datos"""
        logger.error(f"Error de datos: {error}")
        return safe_json_response({
            'error': 'Error de datos',
            'message': str(error)
        }, 400)
    
    @app.errorhandler(HDFSError)
    def handle_hdfs_error(error):
        """Manejo de errores de HDFS"""
        logger.error(f"Error de HDFS: {error}")
        return safe_json_response({
            'error': 'Error de almacenamiento',
            'message': 'Error accediendo al sistema de archivos'
        }, 503)