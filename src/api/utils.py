"""
Utilidades comunes para la API - Importa desde utils.responses
"""
import logging

# Importar desde el módulo responses centralizado
from ..utils.responses import (
    safe_json_response,
    clean_data_for_json,
    validate_query_params,
    format_error_response
)

logger = logging.getLogger(__name__)

# Re-exportar para compatibilidad
__all__ = [
    'safe_json_response',
    'clean_data_for_json',
    'validate_query_params', 
    'format_error_response'
]