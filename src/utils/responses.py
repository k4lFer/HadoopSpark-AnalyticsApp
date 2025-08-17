"""
Utilidades comunes para la API (respuestas JSON, validaciones, etc.)
"""
import math
import logging
from flask import jsonify
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def safe_json_response(data: Any, status_code: int = 200):
    """Crear respuesta JSON segura que maneja NaN, inf, etc."""
    try:
        clean_data = clean_data_for_json(data)
        response = jsonify(clean_data)
        response.status_code = status_code
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta JSON: {e}")
        return jsonify({'error': 'Error procesando respuesta'}), 500


def clean_data_for_json(obj: Any) -> Any:
    """Limpiar datos para que sean serializables en JSON"""
    if isinstance(obj, dict):
        return {k: clean_data_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_data_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, 6)
    elif obj is None:
        return None
    else:
        return obj


def validate_query_params(request, required_params: List[str] = None, optional_params: Dict[str, Any] = None):
    """Validar parámetros de consulta"""
    errors = []
    params = {}
    
    # Validar parámetros requeridos
    if required_params:
        for param in required_params:
            value = request.json.get(param) if request.json else None
            if not value:
                errors.append(f"Parámetro '{param}' es requerido")
            else:
                params[param] = value
    
    # Validar parámetros opcionales con defaults
    if optional_params:
        for param, default_value in optional_params.items():
            value = request.json.get(param) if request.json else None
            params[param] = value if value is not None else default_value
    
    return params, errors


def format_error_response(message: str, details: str = None) -> Dict[str, Any]:
    """Formatear respuesta de error estándar"""
    response = {'error': message}
    if details:
        response['details'] = details
    return response
