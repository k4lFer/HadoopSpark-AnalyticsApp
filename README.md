# Analytics System - Hadoop + Spark + Flask

Sistema completo de analytics con Hadoop, Spark y Flask API para análisis de datos a gran escala con soporte para archivos CSV de hasta 5GB.

## 🏗️ Arquitectura Actual

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Flask API     │    │   Spark Cluster │
│   HTML/JS       │◄──►│   Backend       │◄──►│   + Hadoop      │
│   (Port 5000)   │    │   (Port 5000)   │    │   (Ports 8080+) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Componentes:
- **Frontend**: Dashboard HTML con JavaScript vanilla
- **Backend**: Flask API modular con PySpark
- **Processing**: Apache Spark cluster (1 master + 2 workers)
- **Storage**: Hadoop HDFS para almacenamiento distribuido

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- 8GB+ RAM recomendado
- 10GB+ espacio en disco

### Instalación
```bash
# Clonar repositorio
git clone <tu-repo>
cd analytics-project

# Crear estructura de directorios y generar datos de prueba
make install

# O paso a paso:
make setup    # Crear directorios
make build    # Construir contenedores
make start    # Iniciar servicios
```

### Acceso
- **Dashboard**: http://localhost:5000
- **API REST**: http://localhost:5000/api/*
- **Spark UI**: http://localhost:8080
- **Hadoop UI**: http://localhost:9870
- **Worker 1 UI**: http://localhost:8081
- **Worker 2 UI**: http://localhost:8082

## 📁 Estructura del Proyecto

```
analytics-project/
├── 🐍 Backend (Python/Flask)
│   ├── app.py                 # Aplicación principal (50 líneas)
│   ├── config.py              # Configuración centralizada
│   ├── requirements.txt       # Dependencias Python
│   └── src/                   # Código fuente modular
│       ├── api/               # Endpoints REST (~200 líneas c/u)
│       │   ├── __init__.py    # Registro de blueprints
│       │   ├── health.py      # /api/health
│       │   ├── upload.py      # /api/upload
│       │   ├── query.py       # /api/query, /api/aggregate
│       │   ├── data.py        # /api/sample, /api/stats
│       │   └── utils.py       # Utilidades API
│       │
│       ├── core/              # Lógica de negocio (~150 líneas c/u)
│       │   ├── __init__.py
│       │   ├── analytics_app.py    # Clase principal simplificada
│       │   ├── spark_manager.py    # Gestión Spark
│       │   ├── data_analyzer.py    # Análisis con PySpark
│       │   └── query_engine.py     # Motor SQL
│       │
│       ├── utils/             # Utilidades reutilizables
│       │   ├── __init__.py
│       │   ├── responses.py   # Respuestas JSON
│       │   ├── validators.py  # Validaciones
│       │   └── exceptions.py  # Manejo errores
│       │
│       └── templates/         # Frontend actual
│           └── dashboard.html # Dashboard principal
│
├── 🐳 Docker
│   ├── docker-compose.yml     # Orquestación servicios
│   ├── Dockerfile.flask       # Imagen Python/Spark
│   ├── hadoop.env             # Variables Hadoop
│   └── spark-conf/
│       └── spark-defaults.conf # Configuración Spark
│
└── 🛠️ Herramientas
    ├── Makefile               # Comandos automatizados
    └── README.md              # Este archivo
```

## 🔧 API Endpoints

### 📤 Gestión de Datos
```bash
# Subir archivo CSV (hasta 5GB)
POST /api/upload
Content-Type: multipart/form-data
Body: file=archivo.csv

# Obtener muestra de datos
GET /api/sample?size=100

# Estadísticas del dataset
GET /api/stats

# Información detallada de columnas
GET /api/columns
```

### 🔍 Consultas SQL
```bash
# Ejecutar consulta SQL personalizada
POST /api/query
Content-Type: application/json
Body: {"query": "SELECT * FROM data LIMIT 10", "limit": 1000}

# Realizar agregaciones
POST /api/aggregate
Body: {"group_by": "column", "agg_function": "count"}

# Consultas de ejemplo
GET /api/queries/examples
```

### 🔧 Sistema
```bash
# Estado del sistema
GET /api/health

# Insights automáticos
GET /api/insights
```

## 💻 Desarrollo Local

### Backend (Flask)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Desarrollo sin Docker (Spark local)
export SPARK_MASTER_URL=local[*]
python app.py
```

### Arquitectura Modular del Backend

#### 🔌 `src/api/` - Endpoints REST
- **`health.py`** - Health checks y estado del sistema
- **`upload.py`** - Carga de archivos CSV a HDFS
- **`query.py`** - Consultas SQL y agregaciones
- **`data.py`** - Gestión de datos y estadísticas
- **`utils.py`** - Re-exports desde utils.responses

#### ⚙️ `src/core/` - Lógica de Negocio
- **`analytics_app.py`** - Aplicación principal (orchestrator)
- **`spark_manager.py`** - Gestión de sesiones Spark
- **`data_analyzer.py`** - Análisis de CSV con PySpark
- **`query_engine.py`** - Motor de consultas SQL

#### 🛠️ `src/utils/` - Utilidades
- **`responses.py`** - Respuestas JSON seguras
- **`validators.py`** - Validaciones de entrada
- **`exceptions.py`** - Manejo de errores personalizado

## 🛠️ Comandos Make

### Gestión del Sistema
```bash
make install          # 📦 Instalación completa
make start            # 🚀 Iniciar servicios
make stop             # 🛑 Detener servicios
make restart          # 🔄 Reiniciar servicios
make status           # 📊 Estado de servicios
```

### Desarrollo
```bash
make dev-start        # 🏃 Inicio rápido desarrollo
make dev-restart      # ⚡ Reinicio rápido Flask
make build            # 🔨 Construir contenedores
```

### Monitoreo y Debugging
```bash
make logs             # 📝 Ver todos los logs
make logs-flask       # 🐍 Logs de Flask API
make logs-spark       # ⚡ Logs de Spark
make logs-hadoop      # 🐘 Logs de Hadoop
make monitor          # 📈 Monitoreo de recursos
```

### Mantenimiento
```bash
make clean            # 🧹 Limpiar contenedores
make clean-data       # 🗑️ Limpiar datos HDFS
make backup           # 💾 Backup de datos
make test-api         # 🧪 Probar endpoints
```

### Shell de Debugging
```bash
make shell-flask      # 🐍 Shell del contenedor Flask
make shell-spark      # ⚡ Shell del master Spark
```

## 📊 Configuración de Recursos

### Límites por Contenedor
| Contenedor | RAM | CPU | Descripción |
|------------|-----|-----|-------------|
| Flask API | 4GB | 2 | Backend principal |
| Spark Master | 1GB | 1 | Coordinador Spark |
| Spark Worker 1 | 1.2GB | 2 | Procesador datos |
| Spark Worker 2 | 1.2GB | 2 | Procesador datos |
| Hadoop NameNode | - | - | Metadatos HDFS |
| Hadoop DataNode | - | - | Almacén datos |

### Configuración Spark Optimizada
- **Workers**: 2 workers con 2 cores cada uno
- **Memoria**: 1GB por executor + 2GB driver
- **Particiones**: 4 particiones por defecto
- **Serialización**: JavaSerializer (estabilidad)
- **Límites**: Archivos hasta 5GB

## 🔒 Seguridad y Validaciones

### Validaciones de Entrada
- ✅ Solo archivos CSV (extensión verificada)
- ✅ Tamaño máximo 5GB por archivo
- ✅ Consultas SQL solo de lectura (SELECT/WITH)
- ✅ Validación de nombres de columnas
- ✅ Parámetros de consulta sanitizados

### Seguridad SQL
```python
# ❌ Bloqueadas automáticamente:
DROP TABLE data;
DELETE FROM data;
INSERT INTO data VALUES...;

# ✅ Permitidas:
SELECT * FROM data WHERE column > 100;
WITH temp AS (SELECT...) SELECT * FROM temp;
```

## 📈 Monitoreo y Observabilidad

### URLs de Monitoreo
- **Spark Master**: http://localhost:8080
  - Estado del cluster
  - Aplicaciones activas
  - Workers conectados

- **Hadoop HDFS**: http://localhost:9870
  - Espacio utilizado
  - Archivos almacenados
  - Estado de DataNodes

- **Workers Spark**:
  - Worker 1: http://localhost:8081
  - Worker 2: http://localhost:8082

### Logs y Debugging
```bash
# Ver logs en tiempo real
docker-compose logs -f [servicio]

# Verificar salud del sistema
curl http://localhost:5000/api/health | jq

# Métricas de recursos
docker stats

# Estado de servicios
make status
```

## 🐛 Troubleshooting

### Problemas Comunes

#### ❌ Spark no inicia
```bash
# Verificar memoria disponible
free -h

# Reiniciar cluster Spark
make restart
```

#### ❌ Error "No hay datos cargados"
```bash
# Verificar que el archivo se subió correctamente
curl http://localhost:5000/api/stats

# Ver logs de upload
make logs-flask | grep upload
```

#### ❌ Consulta SQL falla
```bash
# Verificar sintaxis SQL
# Solo SELECT y WITH permitidos
# Tabla siempre se llama 'data'

# Ejemplo correcto:
SELECT column_name, COUNT(*) 
FROM data 
GROUP BY column_name 
LIMIT 100
```

#### ❌ Memoria insuficiente
```bash
# Aumentar memoria en docker-compose.yml
memory: 6G  # Para Flask API

# O reducir tamaño de archivo
# Archivos > 2GB pueden necesitar más memoria
```

### Logs de Debug
```bash
# Logs detallados por servicio
make logs-flask    # Backend Flask
make logs-spark    # Cluster Spark  
make logs-hadoop   # Sistema HDFS

# Verificar configuración Spark
make config-check
```

## 📊 Ejemplos de Uso

### 1. Cargar y Analizar Datos
```bash
# 1. Ir a http://localhost:5000
# 2. Sección "Cargar Datos" 
# 3. Seleccionar archivo CSV
# 4. Click "Cargar Dataset"
# 5. Ver estadísticas automáticas
```

### 2. Consultas SQL de Ejemplo
```sql
-- Conteo total
SELECT COUNT(*) as total_records FROM data;

-- Top categorías
SELECT category, COUNT(*) as count 
FROM data 
GROUP BY category 
ORDER BY count DESC 
LIMIT 10;

-- Estadísticas por grupo
SELECT region, 
       AVG(price) as avg_price,
       SUM(quantity) as total_quantity
FROM data 
GROUP BY region;

-- Filtros complejos
SELECT * FROM data 
WHERE price > 100 
  AND category = 'Electronics'
  AND quantity > 5
ORDER BY price DESC 
LIMIT 50;
```

### 3. Agregaciones Rápidas
```bash
# Via interfaz web:
# 1. Sección "Agregaciones"
# 2. Agrupar por: "category" 
# 3. Función: "count"
# 4. Click "Calcular"

# Via API:
curl -X POST http://localhost:5000/api/aggregate \
  -H "Content-Type: application/json" \
  -d '{"group_by": "category", "agg_function": "count"}'
```

## 🔄 Próximas Mejoras

### 🎯 Roadmap de Desarrollo

#### 📱 Frontend Moderno (Próxima versión)
- **Next.js 13+** con App Router
- **TypeScript** para type safety
- **Tailwind CSS** para styling
- **React Query** para estado de servidor
- **Componentes reutilizables** para visualización

#### 📊 Visualizaciones Avanzadas
- **Charts.js/D3.js** para gráficos interactivos
- **Plotly** para visualizaciones científicas  
- **Dashboard configurable** con widgets
- **Exportación** de gráficos (PNG, PDF)

### 🏗️ Reestructuración para Frontend Separado

Cuando agreguemos Next.js, la estructura será:

```
analytics-project/
├── 🌐 frontend/              # Frontend Next.js
│   ├── src/
│   │   ├── app/             # App Router Next.js 13+
│   │   ├── components/      # Componentes React
│   │   ├── lib/            # Utilidades y API client
│   │   └── hooks/          # Custom hooks
│   ├── package.json
│   ├── next.config.js
│   └── tailwind.config.js
│
├── 🐍 backend/              # Backend Flask (actual src/)
│   ├── app.py
│   ├── config.py  
│   └── src/                # Código actual
│
├── 🐳 infra/               # Infraestructura
│   ├── docker-compose.yml
│   ├── nginx.conf          # Reverse proxy
│   ├── Dockerfile.flask
│   └── Dockerfile.nextjs
│
└── 📚 docs/               # Documentación
    ├── api.md
    ├── deployment.md
    └── development.md
```

## 🤝 Contribuir

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

### Estándares de Código
- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ES6+, funciones puras
- **SQL**: Uppercase keywords, snake_case
- **Docker**: Multi-stage builds, .dockerignore

## 📄 Licencia


## 📞 Soporte

- 🐛 **Issues**: Reportar bugs y solicitar features
- 📖 **Docs**: Documentación detallada en `/docs`
- 💬 **Discussions**: Preguntas y discusiones

---

## ⚡ Quick Start Commands

```bash
# Instalación completa en 3 comandos
git clone https://github.com/tu-usuario/HadoopSpark-AnalyticsApp.git
cd HadoopSpark-AnalyticsApp
make install

# Desarrollo rápido
make dev-start

# Ver estado
make status

# Debugging
make logs-flask
```

**¡Sistema listo en http://localhost:5000!** 🎉