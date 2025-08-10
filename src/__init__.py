# Analytics System - Módulos de utilidades
__version__ = "1.0.0"
__author__ = "Analytics Team"

from .spark_utils import SparkManager, DataAnalyzer, QueryEngine, SAMPLE_QUERIES

__all__ = ['SparkManager', 'DataAnalyzer', 'QueryEngine', 'SAMPLE_QUERIES']