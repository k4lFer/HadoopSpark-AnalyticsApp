"""
Spark Manager modular - Gestión simplificada de Spark
"""
import os
import logging
from typing import Optional, Dict, Any
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

class SparkManager:
    """Manager simplificado para sesión de Spark"""
    
    def __init__(self, app_name: str, master_url: str, spark_conf_dir: str = None):
        self.app_name = app_name
        self.master_url = master_url
        self.spark_conf_dir = spark_conf_dir
        self.spark: Optional[SparkSession] = None
        
        self._initialize()
    
    def _initialize(self):
        """Inicializar sesión de Spark"""
        try:
            logger.info(f"Inicializando Spark: {self.master_url}")
            
            builder = SparkSession.builder \
                .appName(self.app_name) \
                .master(self.master_url)
            
            # Cargar configuración desde archivo si existe
            configs = self._load_spark_config()
            for key, value in configs.items():
                builder = builder.config(key, value)
            
            self.spark = builder.getOrCreate()
            self.spark.sparkContext.setLogLevel("WARN")
            
            self._log_cluster_info()
            logger.info("✅ Spark inicializado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Spark: {e}")
            self.spark = None
    
    def _load_spark_config(self) -> Dict[str, str]:
        """Cargar configuración desde archivo"""
        configs = {}
        
        if not self.spark_conf_dir:
            return self._get_default_config()
        
        config_file = os.path.join(self.spark_conf_dir, 'spark-defaults.conf')
        
        if not os.path.exists(config_file):
            logger.warning(f"Archivo de configuración no encontrado: {config_file}")
            return self._get_default_config()
        
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            key, value = parts
                            configs[key] = value
            
            logger.info(f"✅ Cargadas {len(configs)} configuraciones desde archivo")
            
        except Exception as e:
            logger.error(f"Error leyendo configuración: {e}")
            return self._get_default_config()
        
        return configs
    
    def _get_default_config(self) -> Dict[str, str]:
        """Configuración por defecto mínima"""
        return {
            "spark.serializer": "org.apache.spark.serializer.JavaSerializer",
            "spark.sql.execution.arrow.pyspark.enabled": "false",
            "spark.driver.memory": "1g",
            "spark.executor.memory": "1g",
            "spark.sql.shuffle.partitions": "4"
        }
    
    def _log_cluster_info(self):
        """Mostrar información del cluster"""
        if not self.spark:
            return
        
        try:
            sc = self.spark.sparkContext
            logger.info(f"🔧 Spark UI: {sc.uiWebUrl}")
            logger.info(f"🔧 Master: {sc.master}")
            logger.info(f"🔧 Paralelismo: {sc.defaultParallelism}")
            
        except Exception as e:
            logger.debug(f"Error obteniendo info del cluster: {e}")
    
    def is_available(self) -> bool:
        """Verificar si Spark está disponible"""
        if not self.spark:
            return False
        
        try:
            # Test básico
            self.spark.sql("SELECT 1").collect()
            return True
        except Exception as e:
            logger.warning(f"Spark test failed: {e}")
            return False
    
    def get_session(self) -> Optional[SparkSession]:
        """Obtener sesión de Spark"""
        return self.spark
    
    def get_cluster_resources(self) -> Dict[str, Any]:
        """Obtener información de recursos del cluster"""
        if not self.spark:
            return {}
        
        try:
            sc = self.spark.sparkContext
            #executor_infos = sc.statusTracker().getExecutorInfos()
            
            #total_cores = sum(executor.maxTasks for executor in executor_infos)
            #total_executors = len(executor_infos)

            try:
                executor_infos = sc.statusTracker().getExecutorInfos()
                total_cores = sum(executor.maxTasks for executor in executor_infos)
                total_executors = len(executor_infos)
            except AttributeError:
                # Fallback: usar getExecutorMemoryStatus
                mem_status = sc._jsc.sc().getExecutorMemoryStatus()
                total_executors = mem_status.size()
                # No podemos obtener cores exactos aquí, así que asumimos defaultParallelism
                total_cores = sc.defaultParallelism
            
            return {
                'total_executors': total_executors,
                'total_cores': total_cores,
                'default_parallelism': sc.defaultParallelism,
                'master_url': sc.master,
                'app_id': sc.applicationId,
                'spark_ui_url': sc.uiWebUrl
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo recursos: {e}")
            return {}
    
    def stop(self):
        """Detener sesión de Spark"""
        if self.spark:
            try:
                self.spark.stop()
                logger.info("🛑 Spark session detenida")
            except Exception as e:
                logger.error(f"Error deteniendo Spark: {e}")
        self.spark = None