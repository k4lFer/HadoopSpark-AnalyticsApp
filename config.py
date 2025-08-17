"""
Configuración usando valores hardcodeados (tu configuración actual)
"""
import os

class Config:
    """Configuración base - usando valores fijos como tienes ahora"""
    
    # Flask
    SECRET_KEY = 'analytics-secret-key'
    JSON_SORT_KEYS = False
    
    # Hadoop/HDFS - VALORES FIJOS como tienes ahora
    HADOOP_NAMENODE_URL = 'hdfs://namenode:9000'
    HADOOP_NAMENODE_WEB_URL = 'http://namenode:9870'
    HDFS_USER = 'hdfs'
    
    # Spark - VALORES FIJOS como tienes ahora
    SPARK_MASTER_URL = 'spark://spark-master:7077'
    SPARK_CONF_DIR = '/app/spark-conf'
    SPARK_APP_NAME = 'AnalyticsAPI'
    
    # Archivos
    UPLOAD_FOLDER = '/app/data'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB en bytes
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Límites de consultas
    DEFAULT_QUERY_LIMIT = 1000
    MAX_QUERY_LIMIT = 5000
    DEFAULT_SAMPLE_SIZE = 100
    
    @staticmethod
    def is_allowed_file(filename):
        """Verificar si el archivo es permitido"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}