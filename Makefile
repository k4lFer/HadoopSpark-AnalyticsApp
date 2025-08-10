.PHONY: help build start stop restart logs clean test data

# Variables
COMPOSE_FILE = docker-compose.yml
DATA_SIZE = 100000

help: ## Mostrar ayuda
	@echo "Analytics System - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Configuración inicial del proyecto
	@echo "🔧 Configurando proyecto..."
	@mkdir -p data templates static src logs
	@chmod +x start.sh
	@echo "✅ Configuración completada"

build: ## Construir contenedores
	@echo "🔨 Construyendo contenedores..."
	@docker-compose -f $(COMPOSE_FILE) build

start: ## Iniciar todos los servicios
	@echo "🚀 Iniciando servicios..."
	@docker-compose -f $(COMPOSE_FILE) up -d
	@echo "⏳ Esperando servicios..."
	@sleep 20
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
	@echo "• Spark UI: http://localhost:8080"

logs: ## Ver logs de todos los servicios
	@docker-compose -f $(COMPOSE_FILE) logs -f

logs-flask: ## Ver logs de Flask API
	@docker-compose -f $(COMPOSE_FILE) logs -f flask-api

logs-spark: ## Ver logs de Spark
	@docker-compose -f $(COMPOSE_FILE) logs -f spark-master spark-worker-1

logs-hadoop: ## Ver logs de Hadoop
	@docker-compose -f $(COMPOSE_FILE) logs -f namenode datanode

shell-flask: ## Acceder al shell del contenedor Flask
	@docker-compose -f $(COMPOSE_FILE) exec flask-api /bin/bash

shell-spark: ## Acceder al shell del master de Spark
	@docker-compose -f $(COMPOSE_FILE) exec spark-master /bin/bash

data: ## Generar datos de prueba
	@echo "📊 Generando datos de prueba ($(DATA_SIZE) registros)..."
	@python3 generate_sample_data.py --rows $(DATA_SIZE) --filename data/sample_data.csv
	@echo "✅ Datos generados en data/sample_data.csv"

data-large: ## Generar dataset grande (2M registros)
	@echo "📊 Generando dataset grande (2M registros)..."
	@python3 generate_sample_data.py --large
	@echo "✅ Dataset grande generado"

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

clean-data: ## Limpiar solo datos generados
	@echo "🗑️ Limpiando datos..."
	@rm -rf data/*.csv
	@echo "✅ Datos limpiados"

reset: clean setup data ## Reset completo del sistema
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
dev-start: setup data start ## Inicio rápido para desarrollo
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

# Instalación
install: ## Instalación completa
	@echo "📦 Instalación completa del sistema..."
	@$(MAKE) setup
	@$(MAKE) build
	@$(MAKE) data
	@$(MAKE) start
	@echo ""
	@echo "🎉 ¡Sistema instalado y listo!"
	@echo "Ve a http://localhost:5000 para comenzar"

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
	@echo "• Spark Worker (Puerto 8081)"
	@echo "• PostgreSQL (Puerto 5432)"
	@echo ""
	@echo "Datos:"
	@ls -la data/ 2>/dev/null || echo "Sin datos generados"