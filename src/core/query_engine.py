"""
Query Engine modular - Motor de consultas SQL
"""
import time
import math
import logging
from typing import Dict, List, Tuple, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, isnan, when

from ..utils.exceptions import DataError, SparkError

logger = logging.getLogger(__name__)

class QueryEngine:
    """Motor de consultas SQL simplificado"""
    
    def __init__(self, spark_session: SparkSession):
        self.spark = spark_session
        self.registered_tables: Dict[str, DataFrame] = {}
    
    def register_dataframe(self, df: DataFrame, table_name: str):
        """Registrar DataFrame como tabla temporal"""
        try:
            # Limpiar DataFrame antes de registrar
            clean_df = self._prepare_dataframe_for_sql(df)
            clean_df.createOrReplaceTempView(table_name)
            self.registered_tables[table_name] = clean_df
            
            logger.info(f"Tabla '{table_name}' registrada exitosamente")
            
        except Exception as e:
            logger.error(f"Error registrando tabla {table_name}: {e}")
            raise SparkError(f"Error registrando tabla: {str(e)}")
    
    def execute_sql(self, query: str, limit: int = 1000) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Ejecutar consulta SQL"""
        try:
            logger.info(f"Ejecutando consulta SQL (limit: {limit})")
            
            # Preparar consulta
            prepared_query = self._prepare_query(query, limit)
            logger.debug(f"Query preparada: {prepared_query}")
            
            # Ejecutar con medición de tiempo
            start_time = time.time()
            result_df = self.spark.sql(prepared_query)
            
            # Recolectar resultados de forma segura
            results = self._safe_collect_results(result_df)
            
            execution_time = time.time() - start_time
            logger.info(f"✅ Consulta ejecutada en {execution_time:.2f}s, {len(results)} filas")
            
            return results, None
            
        except Exception as e:
            error_msg = f"Error ejecutando consulta: {str(e)}"
            logger.error(error_msg)
            return None, error_msg
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """Obtener información de una tabla registrada"""
        try:
            if table_name not in self.registered_tables:
                return None
            
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
    
    def _prepare_dataframe_for_sql(self, df: DataFrame) -> DataFrame:
        """Preparar DataFrame para consultas SQL"""
        try:
            # Limpiar valores problemáticos antes de registrar
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
    
    def _prepare_query(self, query: str, limit: int) -> str:
        """Preparar consulta SQL agregando límites si es necesario"""
        query = query.strip()
        
        # Remover punto y coma final si existe
        if query.endswith(';'):
            query = query[:-1]
        
        query_lower = query.lower()
        
        # Solo agregar LIMIT si la consulta no lo tiene
        if 'limit' not in query_lower:
            # Para consultas con GROUP BY, usar límite más conservador
            if 'group by' in query_lower:
                query += f" LIMIT {min(limit, 100)}"
            else:
                query += f" LIMIT {limit}"
        
        return query
    
    def _safe_collect_results(self, df: DataFrame) -> List[Dict]:
        """Recolectar resultados de forma segura"""
        try:
            # Usar collect() para mayor estabilidad
            rows = df.collect()
            
            # Convertir a lista de diccionarios con limpieza
            results = []
            for row in rows:
                row_dict = row.asDict()
                clean_row = {}
                
                for key, value in row_dict.items():
                    clean_row[key] = self._clean_value_for_json(value)
                
                results.append(clean_row)
            
            return results
            
        except Exception as e:
            logger.error(f"Error recolectando resultados: {e}")
            return []
    
    def _clean_value_for_json(self, value):
        """Limpiar valor individual para serialización JSON"""
        if value is None:
            return None
        elif isinstance(value, float):
            if math.isnan(value):
                return None  # Convertir NaN a null
            elif math.isinf(value):
                return None  # Convertir inf a null
            else:
                return round(value, 6)  # Redondear para evitar problemas de precisión
        elif isinstance(value, int) and abs(value) > 2**53:
            return str(value)  # Convertir enteros muy grandes a string
        else:
            return value