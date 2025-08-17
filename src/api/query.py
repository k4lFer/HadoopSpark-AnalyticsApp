"""
API Query - Manejo de consultas SQL y agregaciones
"""
import logging
from flask import Blueprint, request, current_app

from .utils import safe_json_response, validate_query_params, format_error_response
from ..utils.validators import validate_sql_query

logger = logging.getLogger(__name__)
query_bp = Blueprint('query', __name__)

@query_bp.route('/query', methods=['POST'])
def custom_query():
    """Ejecutar consulta SQL personalizada"""
    try:
        # Validar parámetros
        params, errors = validate_query_params(
            request, 
            required_params=['query'],
            optional_params={'limit': current_app.config['DEFAULT_QUERY_LIMIT']}
        )
        
        if errors:
            return safe_json_response(
                format_error_response("Parámetros inválidos", errors), 400
            )
        
        query = params['query'].strip()
        limit = min(params['limit'], current_app.config['MAX_QUERY_LIMIT'])
        
        # Validar consulta SQL
        is_valid, validation_message = validate_sql_query(query)
        if not is_valid:
            return safe_json_response(
                format_error_response(validation_message), 400
            )
        
        # Ejecutar consulta
        analytics = current_app.analytics
        result, error = analytics.execute_query(query, limit)
        
        if error:
            return safe_json_response(format_error_response(error), 400)
        
        return safe_json_response({
            'result': result,
            'query': query,
            'rows_returned': len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"Error en custom_query: {e}")
        return safe_json_response(
            format_error_response(f'Error procesando consulta: {str(e)}'), 500
        )

@query_bp.route('/aggregate', methods=['POST'])
def aggregate_data():
    """Realizar agregaciones usando SQL optimizado"""
    try:
        # Validar parámetros
        params, errors = validate_query_params(
            request,
            required_params=['group_by', 'agg_function'],
            optional_params={'agg_column': None, 'limit': 100}
        )
        
        if errors:
            return safe_json_response(
                format_error_response("Parámetros inválidos", errors), 400
            )
        
        # Construir consulta SQL
        query = _build_aggregation_query(params)
        if not query:
            return safe_json_response(
                format_error_response("No se pudo construir la consulta de agregación"), 400
            )
        
        # Ejecutar agregación
        analytics = current_app.analytics
        result, error = analytics.execute_query(query)
        
        if error:
            return safe_json_response(format_error_response(error), 400)
        
        return safe_json_response({
            'result': result,
            'aggregation': {
                'group_by': params['group_by'],
                'function': params['agg_function'],
                'column': params['agg_column']
            },
            'query_executed': query,
            'rows_returned': len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"Error en aggregate_data: {e}")
        return safe_json_response(
            format_error_response(f'Error en agregación: {str(e)}'), 500
        )

@query_bp.route('/queries/examples')
def get_example_queries():
    """Obtener consultas de ejemplo dinámicas"""
    try:
        analytics = current_app.analytics
        
        if not analytics.has_dataset():
            return safe_json_response(
                format_error_response('No hay datos cargados'), 200
            )
        
        dataset_info = analytics.get_dataset_info()
        columns = dataset_info.get('columns', [])
        
        examples = _generate_example_queries(columns)
        
        return safe_json_response({
            'examples': examples,
            'available_columns': columns
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo ejemplos: {e}")
        return safe_json_response(
            format_error_response(f'Error obteniendo ejemplos: {str(e)}'), 500
        )

def _build_aggregation_query(params: dict) -> str:
    """Construir consulta SQL de agregación"""
    group_by = params['group_by']
    agg_func = params['agg_function']
    agg_col = params['agg_column']
    limit = params['limit']
    
    if agg_func == 'count':
        query = f"SELECT {group_by}, COUNT(*) as count FROM data GROUP BY {group_by} ORDER BY count DESC LIMIT {limit}"
    elif agg_col:
        if agg_func == 'sum':
            query = f"SELECT {group_by}, SUM({agg_col}) as sum_{agg_col} FROM data GROUP BY {group_by} ORDER BY sum_{agg_col} DESC LIMIT {limit}"
        elif agg_func == 'avg':
            query = f"SELECT {group_by}, AVG({agg_col}) as avg_{agg_col} FROM data GROUP BY {group_by} ORDER BY avg_{agg_col} DESC LIMIT {limit}"
        elif agg_func == 'max':
            query = f"SELECT {group_by}, MAX({agg_col}) as max_{agg_col} FROM data GROUP BY {group_by} ORDER BY max_{agg_col} DESC LIMIT {limit}"
        elif agg_func == 'min':
            query = f"SELECT {group_by}, MIN({agg_col}) as min_{agg_col} FROM data GROUP BY {group_by} ORDER BY min_{agg_col} ASC LIMIT {limit}"
        else:
            return None
    else:
        return None
    
    return query

def _generate_example_queries(columns: list) -> dict:
    """Generar consultas de ejemplo basadas en columnas disponibles"""
    examples = {
        'basic': {
            'name': 'Vista General',
            'query': 'SELECT * FROM data LIMIT 10',
            'description': 'Primeras 10 filas del dataset'
        },
        'count': {
            'name': 'Conteo Total',
            'query': 'SELECT COUNT(*) as total_records FROM data',
            'description': 'Número total de registros'
        }
    }
    
    # Agregar ejemplos dinámicos basados en columnas
    if len(columns) > 0:
        first_col = columns[0]
        examples['group_by'] = {
            'name': f'Agrupación por {first_col}',
            'query': f'SELECT {first_col}, COUNT(*) as count FROM data GROUP BY {first_col} LIMIT 10',
            'description': f'Conteo por categorías de {first_col}'
        }
    
    return examples