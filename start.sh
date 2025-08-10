#!/bin/bash

echo "🚀 Iniciando Sistema de Analytics con Hadoop & Spark"
echo "=================================================="

# Crear directorios necesarios
mkdir -p data templates static src

# Copiar archivos de utilidades a src si no existen
if [ ! -f "src/__init__.py" ]; then
    echo "📁 Creando estructura de módulos..."
    # Los archivos ya están creados como artefactos
fi

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está corriendo"
    echo "Por favor inicia Docker Desktop y vuelve a ejecutar este script"
    exit 1
fi

# Verificar si docker-compose está disponible
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose no está instalado"
    echo "Por favor instala docker-compose y vuelve a ejecutar este script"
    exit 1
fi

echo "✅ Docker verificado correctamente"

# Generar datos de prueba si no existen
if [ ! -f "data/sample_data.csv" ]; then
    echo "📊 Generando datos de prueba..."
    python3 generate_sample_data.py --rows 50000 --filename data/sample_data.csv
    echo "✅ Datos de prueba generados"
else
    echo "✅ Datos de prueba ya existen"
fi

# Construir e iniciar contenedores
echo "🔨 Construyendo contenedores..."
docker-compose build

echo "🚀 Iniciando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."

# Función para verificar si un servicio está listo
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f $url > /dev/null 2>&1; then
            echo "✅ $service_name está listo"
            return 0
        fi
        echo "⏳ Esperando $service_name (intento $attempt/$max_attempts)..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name no respondió después de $max_attempts intentos"
    return 1
}

# Verificar servicios
echo "🔍 Verificando servicios..."

check_service "Hadoop NameNode" "http://localhost:9870"
check_service "Spark Master" "http://localhost:8080"
check_service "Flask API" "http://localhost:5000/api/health"

echo ""
echo "🎉 SISTEMA INICIADO CORRECTAMENTE"
echo "=================================="
echo ""
echo "📱 Servicios disponibles:"
echo "• Dashboard Principal: http://localhost:5000"
echo "• Hadoop NameNode UI: http://localhost:9870"
echo "• Spark Master UI: http://localhost:8080"
echo "• Spark Worker UI: http://localhost:8081"
echo ""
echo "🧪 Para probar el sistema:"
echo "1. Ve a http://localhost:5000"
echo "2. Sube el archivo 'data/sample_data.csv'"
echo "3. Ejecuta consultas SQL como:"
echo "   SELECT category, COUNT(*) as total FROM data GROUP BY category"
echo ""
echo "📊 Datos de prueba:"
echo "• Archivo: data/sample_data.csv"
echo "• Registros: $(wc -l < data/sample_data.csv 2>/dev/null || echo 'N/A')"
echo ""
echo "🛠️ Comandos útiles:"
echo "• Ver logs: docker-compose logs -f [servicio]"
echo "• Detener: docker-compose down"
echo "• Reiniciar: docker-compose restart [servicio]"
echo ""

# Mostrar estado de contenedores
echo "📋 Estado de contenedores:"
docker-compose ps

echo ""
echo "✨ ¡Sistema listo para usar!"