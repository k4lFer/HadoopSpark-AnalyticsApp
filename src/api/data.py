"""
API Data - Endpoints para manejo de datos y estadísticas
"""
import logging
from flask import Blueprint, request, current_app

from .utils import safe_json_response, format_error_response

logger = logging.getLogger(__name__)
data_bp = Blueprint('data', __name__)

@data_bp.route('/stats')
def get_stats():
    """Obtener estadísticas completas del dataset actual"""
    try:
        analytics = current_app.analytics
        
        if not analytics.has_dataset():
            return safe_json_response({
                'error': 'No hay datos cargados',
                'message': 'Sube un archivo CSV para comenzar'
            }, 200)
        
        dataset_info = analytics.get_dataset_info()
        insights = _generate_insights(dataset_info)
        
        return safe_json_response({
            'basic_stats': dataset_info,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return safe_json_response(
            format_error_response(f'Error obteniendo estadísticas: {str(e)}'), 500
        )

@data_bp.route('/sample')
def get_sample():
    """Obtener muestra de datos"""
    try:
        analytics = current_app.analytics
        config = current_app.config
        
        if not analytics.has_dataset():
            return safe_json_response(
                format_error_response('No hay datos cargados'), 200
            )
        
        # Obtener tamaño de muestra
        sample_size = request.args.get('size', config['DEFAULT_SAMPLE_SIZE'], type=int)
        sample_size = min(sample_size, 1000)  # Límite máximo
        
        sample, error = analytics.get_sample_data(sample_size)
        
        if error:
            return safe_json_response(format_error_response(error), 400)
        
        # Obtener info de columnas
        dataset_info = analytics.get_dataset_info()
        columns = dataset_info.get('columns', [])
        
        return safe_json_response({
            'sample': sample,
            'size': len(sample) if sample else 0,
            'columns': columns
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo muestra: {e}")
        return safe_json_response(
            format_error_response(f'Error obteniendo muestra: {str(e)}'), 500
        )

@data_bp.route('/columns')
def get_columns():
    """Obtener información detallada de columnas"""
    try:
        analytics = current_app.analytics
        
        if not analytics.has_dataset():
            return safe_json_response(
                format_error_response('No hay datos cargados'), 200
            )
        
        dataset_info = analytics.get_dataset_info()
        columns_info = _build_columns_info(dataset_info)
        
        return safe_json_response({
            'columns': columns_info,
            'total': len(columns_info)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo columnas: {e}")
        return safe_json_response(
            format_error_response(f'Error obteniendo columnas: {str(e)}'), 500
        )

@data_bp.route('/insights')
def get_insights():
    """Obtener insights automáticos del dataset"""
    try:
        analytics = current_app.analytics
        
        if not analytics.has_dataset():
            return safe_json_response(
                format_error_response('No hay datos cargados'), 200
            )
        
        dataset_info = analytics.get_dataset_info()
        insights = _generate_insights(dataset_info)
        
        return safe_json_response(insights)
        
    except Exception as e:
        logger.error(f"Error generando insights: {e}")
        return safe_json_response(
            format_error_response(f'Error generando insights: {str(e)}'), 500
        )

def _build_columns_info(dataset_info: dict) -> list:
    """Construir información detallada de columnas"""
    columns_info = []
    column_types = dataset_info.get('column_types', {})
    null_counts = dataset_info.get('null_counts', {})
    column_stats = dataset_info.get('column_stats', {})
    
    for col_name, col_type in column_types.items():
        col_info = {
            'name': col_name,
            'type': col_type,
            'is_numeric': col_type in ['int', 'double', 'float', 'bigint'],
            'null_count': null_counts.get(col_name, 0),
            'stats': column_stats.get(col_name, {})
        }
        columns_info.append(col_info)
    
    return columns_info

def _generate_insights(dataset_info: dict) -> dict:
    """Generar insights automáticos del dataset"""
    insights = {
        'data_quality': {
            'null_percentages': {},
            'completeness_score': 0
        },
        'summary': {
            'total_rows': dataset_info.get('total_rows', 0),
            'total_columns': dataset_info.get('total_columns', 0),
            'estimated_size_mb': dataset_info.get('estimated_size_mb', 0)
        }
    }
    
    # Calcular completitud de datos
    total_rows = dataset_info.get('total_rows', 0)
    null_counts = dataset_info.get('null_counts', {})
    
    if total_rows > 0 and null_counts:
        null_percentages = {}
        for col, null_count in null_counts.items():
            null_percentage = (null_count / total_rows) * 100
            null_percentages[col] = round(null_percentage, 2)
        
        insights['data_quality']['null_percentages'] = null_percentages
        
        # Score de completitud general
        if null_percentages:
            avg_null_percentage = sum(null_percentages.values()) / len(null_percentages)
            insights['data_quality']['completeness_score'] = round(100 - avg_null_percentage, 2)
    
    return insights