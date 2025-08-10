from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import sys
import logging
import json
import math
from datetime import datetime
from hdfs import InsecureClient
from werkzeug.utils import secure_filename

# Agregar el directorio src al path
sys.path.append('/app/src')

# Importar nuestras utilidades personalizadas
try:
    from spark_utils import SparkManager, DataAnalyzer, QueryEngine, SAMPLE_QUERIES
    logger = logging.getLogger(__name__)
    logger.info("✅ Utilidades de Spark importadas correctamente")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Error importando utilidades de Spark: {e}")
    # Crear clases dummy para evitar errores
    class SparkManager:
        def __init__(self, *args, **kwargs):
            self.spark = None
    class DataAnalyzer:
        def __init__(self, *args, **kwargs):
            pass
    class QueryEngine:
        def __init__(self, *args, **kwargs):
            pass
    SAMPLE_QUERIES = {}

# Configurar logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Configuración
HADOOP_NAMENODE = os.getenv('HADOOP_NAMENODE_URL', 'hdfs://namenode:9000')
SPARK_MASTER = os.getenv('SPARK_MASTER_URL', 'spark://spark-master:7077')
HDFS_WEB_URL = os.getenv('HADOOP_NAMENODE_WEB_URL', 'http://namenode:9870')
HDFS_USER = os.getenv('HDFS_USER', 'hdfs')

# Función personalizada para JSON que maneja NaN
def safe_json_response(data, status_code=200):
    """Crear respuesta JSON segura que maneja NaN, inf, etc."""
    try:
        # Convertir datos problemáticos antes de jsonify
        clean_data = clean_data_for_json(data)
        response = jsonify(clean_data)
        response.status_code = status_code
        return response
    except Exception as e:
        logger.error(f"Error creando respuesta JSON: {e}")
        return jsonify({'error': 'Error procesando respuesta'}), 500

def clean_data_for_json(obj):
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

class AnalyticsApp:
    def __init__(self):
        self.spark_manager = None
        self.data_analyzer = None
        self.query_engine = None
        self.current_dataset = None
        self.initialize()
    
    def initialize(self):
        """Inicializar todos los componentes del sistema"""
        try:
            logger.info("Inicializando Analytics App...")
            
            # Inicializar Spark Manager
            self.spark_manager = SparkManager(
                app_name="AnalyticsAPI_v2",
                master_url=SPARK_MASTER
            )
            
            if self.spark_manager and self.spark_manager.spark:
                # Inicializar analizador de datos
                self.data_analyzer = DataAnalyzer(self.spark_manager.spark)
                
                # Inicializar motor de consultas
                self.query_engine = QueryEngine(self.spark_manager.spark)
                
                logger.info("✅ Todos los componentes inicializados correctamente")
                return True
            else:
                logger.warning("⚠️ Spark no disponible, funcionando en modo limitado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error en inicialización: {e}")
            return False
    
    def load_dataset(self, file_path):
        """Cargar dataset y analizar"""
        try:
            logger.info(f"Cargando dataset: {file_path}")
            
            if not self.data_analyzer:
                return None, "Spark no está disponible. Sistema funcionando en modo limitado."
            
            # Analizar CSV completo
            df, analysis = self.data_analyzer.analyze_csv(file_path)
            
            if df is None:
                return None, "Error cargando archivo CSV"
            
            # Registrar como tabla en el motor de consultas
            if self.query_engine:
                self.query_engine.register_dataframe(df, "data")
            
            # Guardar información del dataset actual
            self.current_dataset = {
                'dataframe': df,
                'analysis': analysis,
                'file_path': file_path
            }
            
            logger.info(f"✅ Dataset cargado: {analysis['total_rows']} filas")
            return analysis, None
            
        except Exception as e:
            logger.error(f"Error cargando dataset: {e}")
            return None, str(e)
    
    def get_system_status(self):
        """Obtener estado del sistema"""
        spark_status = 'ok' if self.spark_manager and self.spark_manager.spark else 'error'
        
        # Verificar conectividad de Spark
        if spark_status == 'ok':
            try:
                self.spark_manager.spark.sql("SELECT 1").collect()
            except Exception as e:
                logger.warning(f"Spark test query failed: {e}")
                spark_status = 'error'
        
        # Verificar HDFS
        hadoop_status = 'ok'
        try:
            client = InsecureClient(HDFS_WEB_URL, user=HDFS_USER)
            client.status('/', strict=False)
        except Exception as e:
            logger.warning(f"HDFS check failed: {e}")
            hadoop_status = 'error'
        
        return {
            'flask': 'ok',
            'spark': spark_status,
            'hadoop': hadoop_status,
            'data_loaded': self.current_dataset is not None,
            'timestamp': datetime.now().isoformat(),
            'spark_mode': 'cluster' if spark_status == 'ok' and 'spark://' in SPARK_MASTER else 'local' if spark_status == 'ok' else 'unavailable'
        }
    
    def execute_query(self, query, limit=1000):
        """Ejecutar consulta SQL"""
        if not self.query_engine:
            return None, "Motor de consultas no disponible - Spark no está inicializado"
        
        if not self.current_dataset:
            return None, "No hay dataset cargado"
        
        return self.query_engine.execute_sql(query, limit)
    
    def get_sample_data(self, sample_size=100):
        """Obtener muestra de datos - VERSIÓN CORREGIDA"""
        if not self.current_dataset:
            return None, "No hay dataset cargado"
        
        if not self.spark_manager or not self.spark_manager.spark:
            return None, "Spark no está disponible"
        
        try:
            df = self.current_dataset['dataframe']
            
            # Usar el método seguro del QueryEngine
            sample_df = df.limit(min(sample_size, 1000))
            sample = self.query_engine._safe_collect_results(sample_df)
            
            return sample, None
        except Exception as e:
            logger.error(f"Error obteniendo muestra: {e}")
            return None, str(e)
    
    def get_quick_insights(self):
        """Obtener insights rápidos del dataset"""
        if not self.current_dataset:
            return None
        
        try:
            analysis = self.current_dataset['analysis']
            
            # Insights automáticos
            insights = {
                'basic_stats': analysis,
                'top_categories': {},
                'data_quality': {
                    'null_percentages': {},
                    'completeness_score': 0
                }
            }
            
            # Calcular completitud de datos
            if 'null_counts' in analysis:
                total_rows = analysis['total_rows']
                null_counts = analysis['null_counts']
                
                for col, null_count in null_counts.items():
                    null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0
                    insights['data_quality']['null_percentages'][col] = round(null_percentage, 2)
                
                # Score de completitud general
                if insights['data_quality']['null_percentages']:
                    avg_null_percentage = sum(insights['data_quality']['null_percentages'].values()) / len(insights['data_quality']['null_percentages'])
                    insights['data_quality']['completeness_score'] = round(100 - avg_null_percentage, 2)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generando insights: {e}")
            return None

# Inicializar aplicación global
analytics_app = AnalyticsApp()

# Rutas de la API
@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('dashboard.html')

@app.route('/api/health')
def health_check():
    """Verificar estado del sistema"""
    return safe_json_response(analytics_app.get_system_status())

@app.route('/api/upload', methods=['POST'])
def upload_data():
    if 'file' not in request.files:
        return safe_json_response({'error': 'No hay archivo en la petición'}, 400)
    
    file = request.files['file']
    if file.filename == '':
        return safe_json_response({'error': 'No se seleccionó archivo'}, 400)
    
    if not file.filename.lower().endswith('.csv'):
        return safe_json_response({'error': 'Solo se permiten archivos CSV'}, 400)
    
    if not analytics_app.spark_manager or not analytics_app.spark_manager.spark:
        return safe_json_response({
            'error': 'Spark no está disponible', 
            'message': 'El sistema está funcionando en modo limitado. Verifica que el cluster Spark esté corriendo.'
        }, 503)
    
    try:
        filename = secure_filename(file.filename)
        local_path = os.path.join('/app/data', filename)
        file.save(local_path)
        
        logger.info(f"Archivo guardado localmente: {local_path}")
        
        # Subir a HDFS
        client = InsecureClient(HDFS_WEB_URL, user=HDFS_USER)
        hdfs_path = f'/user/hdfs/data/{filename}'
        spark_path = f"{HADOOP_NAMENODE}{hdfs_path}"
        
        # Crear carpeta si no existe
        try:
            if not client.status('/user/hdfs/data', strict=False):
                client.makedirs('/user/hdfs/data')
        except:
            client.makedirs('/user/hdfs/data')
        
        client.upload(hdfs_path, local_path, overwrite=True)
        logger.info(f"Archivo subido a HDFS en: {hdfs_path}")
        
        # Leer desde HDFS con Spark
        analysis, error = analytics_app.load_dataset(spark_path)
        
        # Opcional: eliminar archivo local
        try:
            os.remove(local_path)
        except:
            pass
        
        if error:
            return safe_json_response({'error': error}, 500)
        
        insights = analytics_app.get_quick_insights()
        
        return safe_json_response({
            'message': 'Archivo cargado y analizado exitosamente',
            'filename': filename,
            'analysis': analysis,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error en upload: {e}")
        return safe_json_response({'error': f'Error procesando archivo: {str(e)}'}, 500)

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas completas del dataset actual"""
    if not analytics_app.current_dataset:
        return safe_json_response({
            'error': 'No hay datos cargados', 
            'message': 'Sube un archivo CSV para comenzar'
        }, 200)
    
    try:
        insights = analytics_app.get_quick_insights()
        return safe_json_response(insights)
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return safe_json_response({'error': f'Error obteniendo estadísticas: {str(e)}'}, 500)

@app.route('/api/query', methods=['POST'])
def custom_query():
    """Ejecutar consulta SQL personalizada"""
    try:
        data = request.get_json()
        if not data:
            return safe_json_response({'error': 'Datos JSON requeridos'}, 400)
        
        query = data.get('query', '').strip()
        if not query:
            return safe_json_response({'error': 'Query SQL requerido'}, 400)
        
        # Validaciones de seguridad
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in dangerous_keywords):
            return safe_json_response({'error': 'Solo se permiten consultas de lectura (SELECT)'}, 400)
        
        # Verificar que la consulta empiece con SELECT
        if not query_lower.strip().startswith('select'):
            return safe_json_response({'error': 'Solo se permiten consultas SELECT'}, 400)
        
        # Ejecutar consulta (el límite se maneja en QueryEngine)
        result, error = analytics_app.execute_query(query, limit=1000)
        
        if error:
            return safe_json_response({'error': error}, 400)
        
        return safe_json_response({
            'result': result,
            'query': query,
            'rows_returned': len(result) if result else 0,
            'execution_time': 'optimizado'
        })
        
    except Exception as e:
        logger.error(f"Error en custom_query: {e}")
        return safe_json_response({'error': f'Error procesando consulta: {str(e)}'}, 500)

@app.route('/api/sample')
def get_sample():
    """Obtener muestra de datos"""
    try:
        sample_size = request.args.get('size', 100, type=int)
        sample, error = analytics_app.get_sample_data(sample_size)
        
        if error:
            return safe_json_response({'error': error}, 400)
        
        return safe_json_response({
            'sample': sample,
            'size': len(sample) if sample else 0,
            'columns': analytics_app.current_dataset['dataframe'].columns if analytics_app.current_dataset else []
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo muestra: {e}")
        return safe_json_response({'error': f'Error obteniendo muestra: {str(e)}'}, 500)

@app.route('/api/insights')
def get_insights():
    """Obtener insights automáticos del dataset"""
    if not analytics_app.current_dataset:
        return safe_json_response({'error': 'No hay datos cargados'}, 200)
    
    try:
        insights = analytics_app.get_quick_insights()
        return safe_json_response(insights)
    except Exception as e:
        logger.error(f"Error generando insights: {e}")
        return safe_json_response({'error': f'Error generando insights: {str(e)}'}, 500)

@app.route('/api/queries/examples')
def get_example_queries():
    """Obtener consultas de ejemplo"""
    if not analytics_app.current_dataset:
        return safe_json_response({'error': 'No hay datos cargados'}, 200)
    
    try:
        # Adaptar consultas de ejemplo a las columnas disponibles
        columns = analytics_app.current_dataset['dataframe'].columns
        
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
        
        return safe_json_response({
            'examples': examples,
            'available_columns': columns
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo ejemplos: {e}")
        return safe_json_response({'error': f'Error obteniendo ejemplos: {str(e)}'}, 500)

@app.route('/api/columns')
def get_columns():
    """Obtener información detallada de columnas"""
    if not analytics_app.current_dataset:
        return safe_json_response({'error': 'No hay datos cargados'}, 200)
    
    try:
        df = analytics_app.current_dataset['dataframe']
        analysis = analytics_app.current_dataset['analysis']
        
        columns_info = []
        for col_name, col_type in df.dtypes:
            col_info = {
                'name': col_name,
                'type': col_type,
                'is_numeric': col_type in ['int', 'double', 'float', 'bigint'],
                'null_count': analysis.get('null_counts', {}).get(col_name, 0),
                'stats': analysis.get('column_stats', {}).get(col_name, {})
            }
            columns_info.append(col_info)
        
        return safe_json_response({
            'columns': columns_info,
            'total': len(columns_info)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo columnas: {e}")
        return safe_json_response({'error': f'Error obteniendo columnas: {str(e)}'}, 500)

# Agregaciones usando el motor de consultas mejorado
@app.route('/api/aggregate', methods=['POST'])
def aggregate_data():
    """Realizar agregaciones usando SQL optimizado"""
    try:
        data = request.get_json()
        if not data:
            return safe_json_response({'error': 'Datos JSON requeridos'}, 400)
        
        group_by = data.get('group_by', '').strip()
        agg_col = data.get('agg_column', '').strip()
        agg_func = data.get('agg_function', 'count')
        
        if not group_by:
            return safe_json_response({'error': 'Columna de agrupación requerida'}, 400)
        
        # Construir consulta SQL dinámicamente
        if agg_func == 'count':
            query = f"SELECT {group_by}, COUNT(*) as count FROM data GROUP BY {group_by} ORDER BY count DESC LIMIT 100"
        elif agg_col:
            if agg_func == 'sum':
                query = f"SELECT {group_by}, SUM({agg_col}) as sum_{agg_col} FROM data GROUP BY {group_by} ORDER BY sum_{agg_col} DESC LIMIT 100"
            elif agg_func == 'avg':
                query = f"SELECT {group_by}, AVG({agg_col}) as avg_{agg_col} FROM data GROUP BY {group_by} ORDER BY avg_{agg_col} DESC LIMIT 100"
            elif agg_func == 'max':
                query = f"SELECT {group_by}, MAX({agg_col}) as max_{agg_col} FROM data GROUP BY {group_by} ORDER BY max_{agg_col} DESC LIMIT 100"
            elif agg_func == 'min':
                query = f"SELECT {group_by}, MIN({agg_col}) as min_{agg_col} FROM data GROUP BY {group_by} ORDER BY min_{agg_col} ASC LIMIT 100"
            else:
                return safe_json_response({'error': f'Función {agg_func} no soportada'}, 400)
        else:
            return safe_json_response({'error': f'Columna requerida para función {agg_func}'}, 400)
        
        # Ejecutar agregación
        result, error = analytics_app.execute_query(query)
        
        if error:
            return safe_json_response({'error': error}, 400)
        
        return safe_json_response({
            'result': result,
            'aggregation': {
                'group_by': group_by,
                'function': agg_func,
                'column': agg_col if agg_col else None
            },
            'query_executed': query,
            'rows_returned': len(result) if result else 0
        })
        
    except Exception as e:
        logger.error(f"Error en aggregate_data: {e}")
        return safe_json_response({'error': f'Error en agregación: {str(e)}'}, 500)

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return safe_json_response({'error': 'Endpoint no encontrado'}, 404)

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return safe_json_response({'error': 'Error interno del servidor'}, 500)

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('/app/data', exist_ok=True)
    os.makedirs('/app/src', exist_ok=True)
    os.makedirs('/app/templates', exist_ok=True)
    
    logger.info("🚀 Iniciando Analytics API con SparkManager...")
    
    if analytics_app.spark_manager and analytics_app.spark_manager.spark:
        logger.info("✅ Sistema completamente inicializado")
    else:
        logger.warning("⚠️ Sistema iniciado en modo limitado (sin Spark)")
    
    # Ejecutar Flask
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)