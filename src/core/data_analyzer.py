"""
Data Analyzer modular - Análisis de datos con Spark
"""
import logging
import math
from typing import Dict, List, Tuple, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, sum as spark_sum, avg, max as spark_max, min as spark_min, isnan, isnull, when

from ..utils.exceptions import DataError, SparkError

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """Analizador de datos simplificado"""
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
    
    def analyze_csv(self, file_path: str) -> Tuple[Optional[DataFrame], Optional[Dict]]:
        """Analizar archivo CSV"""
        try:
            logger.info(f"Analizando archivo CSV: {file_path}")
            
            # Leer CSV
            df = self._read_csv(file_path)
            if df is None:
                raise DataError("No se pudo leer el archivo CSV")
            
            # Limpiar datos problemáticos
            df = self._clean_dataframe(df)
            
            # Cache para mejor performance
            df.cache()
            
            # Análisis básico
            analysis = self._perform_basic_analysis(df)
            
            logger.info(f"✅ Análisis completado: {analysis['total_rows']} filas, {analysis['total_columns']} columnas")
            
            return df, analysis
            
        except Exception as e:
            logger.error(f"Error analizando CSV: {e}")
            if isinstance(e, (DataError, SparkError)):
                raise
            raise SparkError(f"Error en análisis de datos: {str(e)}")
    
    def _read_csv(self, file_path: str) -> Optional[DataFrame]:
        """Leer archivo CSV con configuración robusta"""
        try:
            df = self.spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .option("multiline", "true") \
                .option("escape", '"') \
                .option("nullValue", "") \
                .option("nanValue", "NaN") \
                .csv(file_path)
            
            # Verificar que el DataFrame no esté vacío
            if df is None:
                return None
            
            # Test básico para verificar que se puede leer
            df.count()  # Esto forzará la evaluación
            
            return df
            
        except Exception as e:
            logger.error(f"Error leyendo CSV: {e}")
            return None
    
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
            # Información básica
            total_rows = df.count()
            columns = df.columns
            total_columns = len(columns)
            
            # Tipos de datos
            column_types = dict(df.dtypes)
            
            # Análisis de valores nulos
            null_counts = self._analyze_null_values(df, columns)
            
            # Estadísticas por columna
            column_stats = self._analyze_numeric_columns(df, column_types)
            
            # Muestra de datos
            sample_data = self._get_sample_data(df, 5)
            
            # Estimación de tamaño
            estimated_size_mb = self._estimate_memory_usage(total_rows, total_columns)
            
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
            return self._get_empty_analysis()
    
    def _analyze_null_values(self, df: DataFrame, columns: List[str]) -> Dict[str, int]:
        """Analizar valores nulos por columna"""
        null_counts = {}
        
        for col_name in columns:
            try:
                null_count = df.filter(col(col_name).isNull()).count()
                null_counts[col_name] = null_count
            except Exception as e:
                logger.warning(f"Error contando nulos en {col_name}: {e}")
                null_counts[col_name] = 0
        
        return null_counts
    
    def _analyze_numeric_columns(self, df: DataFrame, column_types: Dict[str, str]) -> Dict[str, Dict]:
        """Analizar estadísticas de columnas numéricas"""
        column_stats = {}
        numeric_columns = [
            col_name for col_name, col_type in column_types.items() 
            if col_type in ['int', 'bigint', 'double', 'float']
        ]
        
        for col_name in numeric_columns:
            try:
                stats_row = df.select(
                    count(col(col_name)).alias('count'),
                    avg(col(col_name)).alias('mean'),
                    spark_min(col(col_name)).alias('min'),
                    spark_max(col(col_name)).alias('max')
                ).collect()[0]
                
                column_stats[col_name] = {
                    'count': int(stats_row['count']) if stats_row['count'] else 0,
                    'mean': float(stats_row['mean']) if stats_row['mean'] else 0.0,
                    'min': float(stats_row['min']) if stats_row['min'] else 0.0,
                    'max': float(stats_row['max']) if stats_row['max'] else 0.0
                }
                
            except Exception as e:
                logger.warning(f"Error calculando stats para {col_name}: {e}")
                column_stats[col_name] = {}
        
        return column_stats
    
    def _get_sample_data(self, df: DataFrame, limit: int = 5) -> List[Dict]:
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
            # Estimación aproximada: 8 bytes por celda promedio
            bytes_per_cell = 8
            total_bytes = rows * columns * bytes_per_cell
            mb_size = total_bytes / (1024 * 1024)
            return round(mb_size, 2)
        except Exception as e:
            logger.error(f"Error calculando tamaño estimado: {e}")
            return 0.0
    
    def _get_empty_analysis(self) -> Dict:
        """Retornar análisis vacío en caso de error"""
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