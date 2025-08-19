"""
Validadores para la aplicación
"""
import re
from typing import Tuple, Dict, Any, Optional
from flask import Request

def validate_file_upload(request: Request) -> Optional[Dict[str, Any]]:
    """Validar carga de archivo"""
    
    # Verificar que hay archivo en la request
    if 'file' not in request.files:
        return {'error': 'No hay archivo en la petición'}
    
    file = request.files['file']
    
    # Verificar que se seleccionó archivo
    if file.filename == '':
        return {'error': 'No se seleccionó archivo'}
    
    # Verificar extensión
    if not file.filename.lower().endswith('.csv'):
        return {'error': 'Solo se permiten archivos CSV'}
    
    # Verificar tamaño (100MB máximo)
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > 100 * 1024 * 1024:
            return {'error': 'El archivo es demasiado grande. Máximo 100MB.'}
    
    # Todo válido
    return None

def validate_sql_query(query: str) -> Tuple[bool, str]:
    """Validar consulta SQL por seguridad"""
    
    if not query or not query.strip():
        return False, "Consulta vacía"
    
    query_clean = query.lower().strip()
    
    # Palabras clave peligrosas
    dangerous_keywords = [
        'drop', 'delete', 'truncate', 'alter', 'create',
        'insert', 'update', 'grant', 'revoke', 'exec',
        'execute', 'sp_', 'xp_'
    ]
    
    for keyword in dangerous_keywords:
        if re.search(r'\b' + keyword + r'\b', query_clean):
            return False, f"Palabra clave peligrosa detectada: {keyword}"
    
    # Solo permitir SELECT y WITH
    if not (query_clean.startswith('select') or query_clean.startswith('with')):
        return False, "Solo se permiten consultas SELECT y WITH"
    
    # Verificar paréntesis balanceados
    if query.count('(') != query.count(')'):
        return False, "Paréntesis no balanceados"
    
    # Verificar longitud máxima
    if len(query) > 5000:
        return False, "Consulta demasiado larga (máximo 5000 caracteres)"
    
    return True, "Consulta válida"

def validate_column_name(column_name: str) -> bool:
    """Validar nombre de columna"""
    if not column_name:
        return False
    
    # Solo letras, números y guiones bajos
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, column_name))

def validate_aggregation_params(group_by: str, agg_function: str, agg_column: str = None) -> Tuple[bool, str]:
    """Validar parámetros de agregación"""
    
    # Validar group_by
    if not group_by or not validate_column_name(group_by):
        return False, "Columna de agrupación inválida"
    
    # Funciones válidas
    valid_functions = ['count', 'sum', 'avg', 'max', 'min']
    if agg_function not in valid_functions:
        return False, f"Función de agregación inválida. Válidas: {', '.join(valid_functions)}"
    
    # Para funciones que no sean count, necesitamos columna
    if agg_function != 'count':
        if not agg_column or not validate_column_name(agg_column):
            return False, f"Columna requerida para función {agg_function}"
    
    return True, "Parámetros válidos"

def sanitize_filename(filename: str) -> str:
    """Limpiar nombre de archivo"""
    if not filename:
        return "file"
    
    # Remover caracteres peligrosos
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limitar longitud
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:90] + ('.' + ext if ext else '')
    
    return filename

def validate_limit(limit_str: str, max_limit: int = 5000) -> Tuple[bool, int]:
    """Validar parámetro de límite"""
    try:
        limit = int(limit_str)
        if limit < 1:
            return False, 1
        if limit > max_limit:
            return False, max_limit
        return True, limit
    except (ValueError, TypeError):
        return False, 100  # Default