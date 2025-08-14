.PHONY: help build start stop restart logs clean test data

# Variables
COMPOSE_FILE = docker-compose.yml
DATA_SIZE = 100000

help: ## Mostrar ayuda
	@echo "Analytics System - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $1, $2}'

setup: ## Configuración inicial del proyecto
	@echo "🔧 Configurando proyecto..."
	@mkdir -p templates static src logs spark-conf
	@chmod +x start.sh
	@echo "✅ Configuración completada"

build: ## Construir contenedores
	@echo "🔨 Construyendo contenedores..."
	@docker-compose -f $(COMPOSE_FILE) build

start: ## Iniciar todos los servicios
	@echo "🚀 Iniciando servicios..."
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "⏳ Esperando servicios..."
	@sleep 30
	@$(MAKE) status

stop: ## Detener todos los servicios
	@echo "🛑 Deteniendo servicios..."
	@docker-compose -f $(COMPOSE_FILE) down

restart: ## Reiniciar todos los servicios
	@echo "🔄 Reiniciando servicios..."
	@docker-compose -f $(COMPOSE_FILE) restart

status: ## Mostrar estado de servicios
	@echo "📊 Estado de servicios:"
	@docker-compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "🌐 URLs disponibles:"
	@echo "• Dashboard: http://localhost:5000"
	@echo "• Hadoop UI: http://localhost:9870"
	@echo "• Spark Master UI: http://localhost:8080"
	@echo "• Spark Worker 1 UI: http://localhost:8081"
	@echo "• Spark Worker 2 UI: http://localhost:8082"

logs: ## Ver logs de todos los servicios
	@docker-compose -f $(COMPOSE_FILE) logs -f

logs-flask: ## Ver logs de Flask API
	@docker-compose -f $(COMPOSE_FILE) logs -f flask-api

logs-spark: ## Ver logs de Spark
	@docker-compose -f $(COMPOSE_FILE) logs -f spark-master spark-worker-1 spark-worker-2

logs-hadoop: ## Ver logs de Hadoop
	@docker-compose -f $(COMPOSE_FILE) logs -f namenode datanode

shell-flask: ## Acceder al shell del contenedor Flask
	@docker-compose -f $(COMPOSE_FILE) exec flask-api /bin/bash

shell-spark: ## Acceder al shell del master de Spark
	@docker-compose -f $(COMPOSE_FILE) exec spark-master /bin/bash

test-api: ## Probar endpoints de la API
	@echo "🧪 Probando API..."
	@echo "Health check:"
	@curl -s http://localhost:5000/api/health | python3 -m json.tool || echo "❌ API no disponible"
	@echo ""
	@echo "Stats endpoint:"
	@curl -s http://localhost:5000/api/stats | python3 -m json.tool || echo "❌ No hay datos cargados"

clean: ## Limpiar contenedores y volúmenes
	@echo "🧹 Limpiando sistema..."
	@docker-compose -f $(COMPOSE_FILE) down -v
	@docker system prune -f
	@echo "✅ Sistema limpiado"

clean-data: ## Limpiar solo datos subidos
	@echo "🗑️ Limpiando datos subidos..."
	@docker-compose -f $(COMPOSE_FILE) exec namenode hdfs dfs -rm -r /user/hdfs/data/* 2>/dev/null || echo "No hay datos en HDFS"
	@echo "✅ Datos limpiados"

reset: clean setup ## Reset completo del sistema
	@echo "🔄 Reset completo realizado"

monitor: ## Monitorear recursos del sistema
	@echo "📈 Monitoreando recursos..."
	@docker stats

backup: ## Hacer backup de datos
	@echo "💾 Creando backup..."
	@mkdir -p backups
	@tar -czf backups/data_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/
	@echo "✅ Backup creado en backups/"

# Comandos de desarrollo
dev-start: setup start ## Inicio rápido para desarrollo
	@echo "🚀 Entorno de desarrollo listo"

dev-restart: ## Reinicio rápido para desarrollo
	@docker-compose -f $(COMPOSE_FILE) restart flask-api
	@echo "🔄 Flask API reiniciada"

# Pruebas específicas
test-spark: ## Probar conexión a Spark
	@echo "⚡ Probando Spark..."
	@docker-compose -f $(COMPOSE_FILE) exec spark-master spark-submit --version

test-hadoop: ## Probar conexión a Hadoop
	@echo "🐘 Probando Hadoop..."
	@docker-compose -f $(COMPOSE_FILE) exec namenode hdfs dfsadmin -report

test-workers: ## Verificar workers de Spark
	@echo "👷 Verificando workers de Spark..."
	@curl -s http://localhost:8080 | grep -o "worker-[0-9]*" || echo "Verificar manualmente en http://localhost:8080"

# Configuración
config-check: ## Verificar configuración de Spark
	@echo "🔍 Verificando configuración de Spark..."
	@echo "Contenido de spark-defaults.conf:"
	@cat spark-conf/spark-defaults.conf 2>/dev/null || echo "❌ Archivo no encontrado"
	@echo ""
	@echo "Verificando montaje en contenedor:"
	@docker-compose -f $(COMPOSE_FILE) exec flask-api ls -la /app/spark-conf/ 2>/dev/null || echo "❌ Contenedor no está corriendo"

# Instalación
install: ## Instalación completa
	@echo "📦 Instalación completa del sistema..."
	@$(MAKE) setup
	@$(MAKE) build
	@$(MAKE) start
	@echo ""
	@echo "🎉 ¡Sistema instalado y listo!"
	@echo "Ve a http://localhost:5000 para comenzar"
	@echo "Sube un archivo CSV para empezar a analizar datos"

# Información del sistema
info: ## Mostrar información del sistema
	@echo "ℹ️ Información del Sistema Analytics"
	@echo "=================================="
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker-compose --version)"
	@echo "Servicios configurados:"
	@echo "• Flask API (Puerto 5000)"
	@echo "• Hadoop NameNode (Puerto 9870)"
	@echo "• Spark Master (Puerto 8080)"
	@echo "• Spark Worker 1 (Puerto 8081)"
	@echo "• Spark Worker 2 (Puerto 8082)"
	@echo ""
	@echo "Configuración de recursos (por worker):"
	@echo "• CPU: 2 cores máximo"
	@echo "• RAM: 1GB máximo"
	@echo ""
	@echo "Para subir datos: Ve a http://localhost:5000 y usa la sección 'Cargar Datos'"

# Comandos para debugging
debug-spark-config: ## Mostrar configuración actual de Spark
	@echo "🔧 Configuración de Spark en contenedores:"
	@docker-compose -f $(COMPOSE_FILE) exec spark-master printenv | grep SPARK || true
	@echo ""
	@echo "Variables de worker:"
	@docker-compose -f $(COMPOSE_FILE) exec spark-worker-1 printenv | grep SPARK || true

debug-resources: ## Mostrar uso de recursos
	@echo "📊 Uso de recursos por contenedor:"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

purge: ## Eliminar absolutamente todo de Docker (contenedores, imágenes, volúmenes, redes, builds)
	@echo "🔥 Eliminando TODO de Docker..."
	@docker stop $$(docker ps -aq) 2>/dev/null || true
	@docker rm -f $$(docker ps -aq) 2>/dev/null || true
	@docker volume rm $$(docker volume ls -q) 2>/dev/null || true
	@docker network rm $$(docker network ls -q) 2>/dev/null || true
	@docker image rm -f $$(docker images -aq) 2>/dev/null || true
	@docker builder prune -a --force
	@docker system prune -a --volumes -f
	@echo "✅ Limpieza total completada"
