"""
Aplicación principal de Analytics - Versión modular
"""
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

from .spark_manager import SparkManager
from .data_analyzer import DataAnalyzer
from .query_engine import QueryEngine

logger = logging.getLogger(__name__)

class AnalyticsApp:
    
    def __init__(self, config_class):
        self.config = config_class
        self.spark_manager: Optional[SparkManager] = None
        self.data_analyzer: Optional[DataAnalyzer] = None
        self.query_engine: Optional[QueryEngine] = None
        self.current_dataset: Optional[Dict] = None
        
        self._initialize()
    
    def _initialize(self):
        try:
            logger.info("Inicializando Analytics App...")
            
            self.spark_manager = SparkManager(
                app_name=self.config.SPARK_APP_NAME,
                master_url=self.config.SPARK_MASTER_URL,
                spark_conf_dir=self.config.SPARK_CONF_DIR
            )
            
            if self.spark_manager.is_available():
                spark_session = self.spark_manager.get_session()
                self.data_analyzer = DataAnalyzer(spark_session)
                self.query_engine = QueryEngine(spark_session)
                logger.info("✅ Todos los componentes inicializados")
            else:
                logger.warning("⚠️ Spark no disponible - modo limitado")
                
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
    
    def is_healthy(self) -> bool:
        """Verificar si el sistema está saludable"""
        return (self.spark_manager is not None and 
                self.spark_manager.is_available() and
                self.data_analyzer is not None and
                self.query_engine is not None)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        spark_status = 'ok' if self.is_healthy() else 'error'
        
        return {
            'flask': 'ok',
            'spark': spark_status,
            'data_loaded': self.current_dataset is not None,
            'timestamp': datetime.now().isoformat(),
            'spark_mode': self._get_spark_mode()
        }
    
    def _get_spark_mode(self) -> str:
        """Determinar modo de Spark"""
        if not self.is_healthy():
            return 'unavailable'
        
        master_url = self.config.SPARK_MASTER_URL
        if 'spark://' in master_url:
            return 'cluster'
        elif 'local' in master_url:
            return 'local'
        else:
            return 'unknown'
    
    def get_cluster_info(self) -> Optional[str]:
        """Obtener información del cluster"""
        if not self.is_healthy():
            return None
            
        try:
            resources = self.spark_manager.get_cluster_resources()
            if resources:
                return f"{resources.get('total_executors', 0)} executors, {resources.get('total_cores', 0)} cores totales"
        except Exception as e:
            logger.warning(f"Error obteniendo info cluster: {e}")
        
        return None
    
    def load_dataset(self, file_path: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Cargar dataset desde archivo"""
        if not self.is_healthy():
            return None, "Spark no está disponible"
        
        try:
            df, analysis = self.data_analyzer.analyze_csv(file_path)
            
            if df is None:
                return None, "Error analizando archivo CSV"
            
            # Registrar en query engine
            self.query_engine.register_dataframe(df, "data")
            
            # Guardar dataset actual
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
    
    def execute_query(self, query: str, limit: int = None) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Ejecutar consulta SQL"""
        if not self.is_healthy():
            return None, "Motor de consultas no disponible"
        
        if not self.current_dataset:
            return None, "No hay dataset cargado"
        
        limit = limit or self.config.DEFAULT_QUERY_LIMIT
        return self.query_engine.execute_sql(query, limit)
    
    def get_sample_data(self, sample_size: int = None) -> Tuple[Optional[List[Dict]], Optional[str]]:
        """Obtener muestra de datos"""
        if not self.current_dataset:
            return None, "No hay dataset cargado"
        
        sample_size = sample_size or self.config.DEFAULT_SAMPLE_SIZE
        
        try:
            df = self.current_dataset['dataframe']
            sample_df = df.limit(min(sample_size, 1000))
            sample = self.query_engine._safe_collect_results(sample_df)
            return sample, None
            
        except Exception as e:
            logger.error(f"Error obteniendo muestra: {e}")
            return None, str(e)
    
    def get_dataset_info(self) -> Optional[Dict]:
        """Obtener información del dataset actual"""
        if not self.current_dataset:
            return None
        
        return self.current_dataset['analysis']
    
    def has_dataset(self) -> bool:
        """Verificar si hay dataset cargado"""
        return self.current_dataset is not None
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.spark_manager:
            self.spark_manager.stop()
        self.current_dataset = None
        logger.info("🧹 Recursos limpiados")