"""
Utilidades para manejo de Spark - VERSIÓN SIMPLIFICADA QUE USA CONFIGURACIÓN EXTERNA
"""
import logging
import time
import json
import math
import os
from typing import Dict, List, Tuple, Optional, Any
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, lit, count, sum as spark_sum, avg, max as spark_max, min as spark_min, isnan, isnull, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# Configurar logging
logger = logging.getLogger(__name__)

class SparkManager:
    """Manager para la sesión de Spark - USA CONFIGURACIÓN EXTERNA"""
    
    def __init__(self, app_name: str = "AnalyticsApp", master_url: str = "local[*]"):
        self.app_name = app_name
        self.master_url = master_url
        self.spark = None
        self.spark_conf_dir = os.getenv('SPARK_CONF_DIR', '/app/spark-conf')
        self.initialize_spark()
    
    def initialize_spark(self):
        """Inicializar sesión de Spark usando archivo de configuración"""
        try:
            logger.info(f"Inicializando Spark con master: {self.master_url}")
            logger.info(f"Usando configuración de: {self.spark_conf_dir}")
            
            # Configuración base - MÍNIMA
            builder = SparkSession.builder \
                .appName(self.app_name) \
                .master(self.master_url)
            
            # Verificar si existe archivo de configuración
            spark_defaults_path = os.path.join(self.spark_conf_dir, 'spark-defaults.conf')
            if os.path.exists(spark_defaults_path):
                logger.info(f"✅ Encontrado archivo de configuración: {spark_defaults_path}")
                
                # Leer configuración desde archivo
                config_overrides = self._load_spark_config(spark_defaults_path)
                
                # Aplicar configuraciones del archivo
                for key, value in config_overrides.items():
                    builder = builder.config(key, value)
                    
                logger.info(f"✅ Aplicadas {len(config_overrides)} configuraciones desde archivo")
            else:
                logger.warning(f"⚠️ Archivo de configuración no encontrado: {spark_defaults_path}")
                logger.info("Usando configuración por defecto mínima")
                
                # Solo configuraciones esenciales si no hay archivo
                essential_configs = {
                    "spark.serializer": "org.apache.spark.serializer.JavaSerializer",
                    "spark.sql.execution.arrow.pyspark.enabled": "false",
                    "spark.driver.memory": "1g",
                    "spark.executor.memory": "1g",
                    "spark.sql.shuffle.partitions": "4"
                }
                
                for key, value in essential_configs.items():
                    builder = builder.config(key, value)
            
            # Crear sesión
            self.spark = builder.getOrCreate()
            
            # Configurar nivel de logging
            self.spark.sparkContext.setLogLevel("WARN")
            
            # Mostrar información del cluster
            self._log_cluster_info()
            
            logger.info("✅ Spark inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Spark: {e}")
            self.spark = None
            return False
    
    def _load_spark_config(self, config_file: str) -> Dict[str, str]:
        """Cargar configuración desde archivo spark-defaults.conf"""
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Ignorar comentarios y líneas vacías
                    if line and not line.startswith('#'):
                        parts = line.split(None, 1)  # Split en primer espacio
                        if len(parts) == 2:
                            key, value = parts
                            config[key] = value
                            
            logger.info(f"✅ Cargadas {len(config)} configuraciones desde {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"❌ Error leyendo configuración de {config_file}: {e}")
            return {}
    
    def _log_cluster_info(self):
        """Mostrar información del cluster Spark"""
        try:
            sc = self.spark.sparkContext
            logger.info(f"🔧 Spark UI disponible en: {sc.uiWebUrl}")
            logger.info(f"🔧 Aplicación ID: {sc.applicationId}")
            logger.info(f"🔧 Master URL: {sc.master}")
            logger.info(f"🔧 Paralelismo por defecto: {sc.defaultParallelism}")
            
            # Información de executors (si está disponible)
            try:
                executor_infos = sc.statusTracker().getExecutorInfos()
                logger.info(f"🔧 Número de executors: {len(executor_infos)}")
                for executor in executor_infos:
                    logger.info(f"  - Executor {executor.executorId}: {executor.maxTasks} tasks máximas")
            except Exception as e:
                logger.debug(f"No se pudo obtener info de executors: {e}")
                
        except Exception as e:
            logger.warning(f"Error obteniendo información del cluster: {e}")
    
    def get_session(self) -> Optional[SparkSession]:
        """Obtener la sesión de Spark"""
        return self.spark
    
    def get_cluster_resources(self) -> Dict[str, Any]:
        """Obtener información de recursos del cluster"""
        if not self.spark:
            return {}
        
        try:
            sc = self.spark.sparkContext
            executor_infos = sc.statusTracker().getExecutorInfos()
            
            total_cores = sum(executor.maxTasks for executor in executor_infos)
            total_executors = len(executor_infos)
            
            return {
                'total_executors': total_executors,
                'total_cores': total_cores,
                'default_parallelism': sc.defaultParallelism,
                'master_url': sc.master,
                'app_id': sc.applicationId,
                'spark_ui_url': sc.uiWebUrl
            }
        except Exception as e:
            logger.error(f"Error obteniendo recursos del cluster: {e}")
            return {}
    
    def stop(self):
        """Detener la sesión de Spark"""
        if self.spark:
            self.spark.stop()
            logger.info("🛑 Spark session detenida")


class DataAnalyzer:
    """Analizador de datos usando Spark - SIN CAMBIOS EN LA LÓGICA"""
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        
    def analyze_csv(self, file_path: str) -> Tuple[Optional[DataFrame], Optional[Dict]]:
        """
        Analizar archivo CSV y retornar DataFrame y análisis estadístico
        """
        try:
            logger.info(f"Analizando archivo CSV: {file_path}")
            
            # Leer CSV con configuración robusta
            df = self.spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .option("multiline", "true") \
                .option("escape", '"') \
                .option("nullValue", "") \
                .option("nanValue", "NaN") \
                .csv(file_path)
            
            if df is None:
                logger.error("Error: DataFrame es None")
                return None, None
            
            # Limpiar datos problemáticos ANTES de cualquier operación
            df = self._clean_dataframe(df)
            
            # Cache del DataFrame para mejorar performance
            df.cache()
            
            # Análisis básico
            analysis = self._perform_basic_analysis(df)
            
            logger.info(f"✅ Análisis completado: {analysis['total_rows']} filas, {analysis['total_columns']} columnas")
            
            return df, analysis
            
        except Exception as e:
            logger.error(f"Error analizando CSV: {e}")
            return None, None
    
    def _clean_dataframe(self, df: DataFrame) -> DataFrame:
        """Limpiar DataFrame de valores problemáticos"""
        try:
            # Reemplazar NaN, inf, -inf con null en columnas numéricas
            for col_name, col_type in df.dtypes:
                if col_type in ['double', 'float']:
                    df = df.withColumn(
                        col_name,
                        when(
                            isnan(col(col_name)) | 
                            col(col_name).isin(float('inf'), float('-inf')),
                            None
                        ).otherwise(col(col_name))
                    )
            
            return df
            
        except Exception as e:
            logger.error(f"Error limpiando DataFrame: {e}")
            return df
    
    def _perform_basic_analysis(self, df: DataFrame) -> Dict:
        """Realizar análisis básico del DataFrame"""
        try:
            # Conteo básico
            total_rows = df.count()
            columns = df.columns
            total_columns = len(columns)
            
            # Tipos de datos
            column_types = dict(df.dtypes)
            
            # Análisis de valores nulos (simplificado)
            null_counts = {}
            for col_name in columns:
                try:
                    null_count = df.filter(col(col_name).isNull()).count()
                    null_counts[col_name] = null_count
                except Exception as e:
                    logger.warning(f"Error contando nulos en {col_name}: {e}")
                    null_counts[col_name] = 0
            
            # Estadísticas por columna (solo numéricas, simplificado)
            column_stats = {}
            numeric_columns = [col_name for col_name, col_type in df.dtypes 
                             if col_type in ['int', 'bigint', 'double', 'float']]
            
            for col_name in numeric_columns:
                try:
                    stats_df = df.select(
                        count(col(col_name)).alias('count'),
                        avg(col(col_name)).alias('mean'),
                        spark_min(col(col_name)).alias('min'),
                        spark_max(col(col_name)).alias('max')
                    ).collect()[0]
                    
                    column_stats[col_name] = {
                        'count': int(stats_df['count']) if stats_df['count'] else 0,
                        'mean': float(stats_df['mean']) if stats_df['mean'] else 0.0,
                        'min': float(stats_df['min']) if stats_df['min'] else 0.0,
                        'max': float(stats_df['max']) if stats_df['max'] else 0.0
                    }
                except Exception as e:
                    logger.warning(f"Error calculando stats para {col_name}: {e}")
                    column_stats[col_name] = {}
            
            # Muestra de datos
            sample_data = self._get_clean_sample(df, 5)
            
            # Estimar tamaño en memoria
            try:
                estimated_size_mb = self._estimate_memory_usage(total_rows, total_columns)
            except Exception as e:
                logger.warning(f"Error estimando memoria: {e}")
                estimated_size_mb = 0.0
            
            return {
                'total_rows': total_rows,
                'total_columns': total_columns,
                'columns': columns,
                'column_types': column_types,
                'null_counts': null_counts,
                'column_stats': column_stats,
                'sample_data': sample_data,
                'estimated_size_mb': estimated_size_mb
            }
            
        except Exception as e:
            logger.error(f"Error en análisis básico: {e}")
            return {
                'total_rows': 0,
                'total_columns': 0,
                'columns': [],
                'column_types': {},
                'null_counts': {},
                'column_stats': {},
                'sample_data': [],
                'estimated_size_mb': 0.0
            }
    
    def _get_clean_sample(self, df: DataFrame, limit: int = 5) -> List[Dict]:
        """Obtener muestra limpia de datos"""
        try:
            sample_rows = df.limit(limit).collect()
            
            clean_sample = []
            for row in sample_rows:
                row_dict = row.asDict()
                clean_row = {}
                for key, value in row_dict.items():
                    if value is None:
                        clean_row[key] = None
                    elif isinstance(value, float):
                        if math.isnan(value) or math.isinf(value):
                            clean_row[key] = None
                        else:
                            clean_row[key] = round(value, 4)
                    else:
                        clean_row[key] = value
                clean_sample.append(clean_row)
            
            return clean_sample
            
        except Exception as e:
            logger.error(f"Error obteniendo muestra: {e}")
            return []
    
    def _estimate_memory_usage(self, rows: int, columns: int) -> float:
        """Estimar uso de memoria en MB"""
        try:
            bytes_per_cell = 8
            total_bytes = rows * columns * bytes_per_cell
            mb_size = total_bytes / (1024 * 1024)
            return round(mb_size, 2)
        except Exception as e:
            logger.error(f"Error calculando tamaño estimado: {e}")
            return 0.0


class QueryEngine:
    """Motor de consultas SQL usando Spark - SIN CAMBIOS EN LA LÓGICA"""
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        self.registered_tables = {}
        
    def register_dataframe(self, df: DataFrame, table_name: str):
        """Registrar DataFrame como tabla temporal"""
        try:
            clean_df = self._prepare_dataframe_for_sql(df)
            clean_df.createOrReplaceTempView(table_name)
            self.registered_tables[table_name] = clean_df
            logger.info(f"Tabla '{table_name}' registrada exitosamente")
        except Exception as e:
            logger.error(f"Error registrando tabla {table_name}: {e}")
    
    def _prepare_dataframe_for_sql(self, df: DataFrame) -> DataFrame:
        """Preparar DataFrame para consultas SQL"""
        try:
            for col_name, col_type in df.dtypes:
                if col_type in ['double', 'float']:
                    df = df.withColumn(
                        col_name,
                        when(
                            isnan(col(col_name)) | 
                            col(col_name).isin(float('inf'), float('-inf')),
                            None
                        ).otherwise(col(col_name))
                    )
            return df
        except Exception as e:
            logger.error(f"Error preparando DataFrame: {e}")
            return df
    
    def execute_sql(self, query: str, limit: int = 1000) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Ejecutar consulta SQL y retornar resultados"""
        try:
            logger.info(f"Ejecutando consulta SQL (limit: {limit})")
            
            query = query.strip()
            if query.endswith(';'):
                query = query[:-1]
            
            query_lower = query.lower()
            
            if 'limit' not in query_lower:
                if 'group by' in query_lower:
                    query += f" LIMIT {min(limit, 100)}"
                else:
                    query += f" LIMIT {limit}"
            
            logger.info(f"Query final: {query}")
            
            start_time = time.time()
            result_df = self.spark.sql(query)
            
            results = self._safe_collect_results(result_df)
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Consulta ejecutada en {execution_time:.2f}s, {len(results)} filas")
            
            return results, None
            
        except Exception as e:
            error_msg = f"Error ejecutando consulta: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def _safe_collect_results(self, df: DataFrame) -> List[Dict]:
        """Recolectar resultados de forma segura"""
        try:
            rows = df.collect()
            
            results = []
            for row in rows:
                row_dict = row.asDict()
                clean_row = {}
                
                for key, value in row_dict.items():
                    if value is None:
                        clean_row[key] = None
                    elif isinstance(value, float):
                        if math.isnan(value):
                            clean_row[key] = None
                        elif math.isinf(value):
                            clean_row[key] = None
                        else:
                            clean_row[key] = round(value, 6)
                    elif isinstance(value, int) and abs(value) > 2**53:
                        clean_row[key] = str(value)
                    else:
                        clean_row[key] = value
                
                results.append(clean_row)
            
            return results
            
        except Exception as e:
            logger.error(f"Error recolectando resultados: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Obtener información de una tabla"""
        try:
            if table_name in self.registered_tables:
                df = self.registered_tables[table_name]
                return {
                    'name': table_name,
                    'columns': df.columns,
                    'dtypes': dict(df.dtypes),
                    'count': df.count()
                }
        except Exception as e:
            logger.error(f"Error obteniendo info de tabla {table_name}: {e}")
        return None


# Consultas de ejemplo predefinidas - SIN CAMBIOS
SAMPLE_QUERIES = {
    'basic_count': {
        'name': 'Conteo Total',
        'query': 'SELECT COUNT(*) as total_records FROM data',
        'description': 'Cuenta el número total de registros'
    },
    'sample_data': {
        'name': 'Muestra de Datos',
        'query': 'SELECT * FROM data LIMIT 10',
        'description': 'Primeras 10 filas del dataset'
    },
    'column_stats': {
        'name': 'Estadísticas de Columnas',
        'query': 'DESCRIBE data',
        'description': 'Información sobre las columnas'
    }
}

# Funciones de utilidad - SIN CAMBIOS
def create_spark_manager(app_name: str = "AnalyticsApp", master_url: str = "local[*]") -> SparkManager:
    """Factory function para crear SparkManager"""
    return SparkManager(app_name, master_url)

def validate_sql_query(query: str) -> Tuple[bool, str]:
    """Validar si una consulta SQL es segura"""
    dangerous_keywords = [
        'drop', 'delete', 'truncate', 'alter', 'create', 
        'insert', 'update', 'grant', 'revoke'
    ]
    
    query_lower = query.lower().strip()
    
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            return False, f"Palabra clave peligrosa detectada: {keyword}"
    
    if not query_lower.startswith('select') and not query_lower.startswith('with'):
        return False, "Solo se permiten consultas SELECT y WITH"
    
    return True, "Consulta válida"

def format_results_for_display(results: List[Dict], max_rows: int = 100) -> List[Dict]:
    """Formatear resultados para mostrar en la interfaz"""
    if not results:
        return []
    
    # Limitar número de filas
    display_results = results[:max_rows]
    
    # Formatear valores para mejor visualización
    for row in display_results:
        for key, value in row.items():
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    row[key] = None
                else:
                    row[key] = round(value, 4)
            elif value is None:
                row[key] = None  # Mantener como None para JSON
    
    return display_results