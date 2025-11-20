#!/bin/bash

# ========================================
# SCRIPT PARA CARGAR VARIABLES DE ENTORNO
# ========================================
# Este script carga las variables desde el archivo .env
# Uso: source /path/to/load-env.sh

# Detectar la ruta del proyecto
if [ -z "$PROJECT_ROOT" ]; then
    # Intentar detectar desde la ubicación del script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

ENV_FILE="$PROJECT_ROOT/.env"

# Verificar que existe el archivo .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: No se encontró el archivo .env en $ENV_FILE"
    echo "   Por favor, ejecuta primero el script quickstart.sh para configurar el sistema."
    exit 1
fi

# Cargar variables de entorno desde .env
# Ignora líneas vacías y comentarios
set -a  # Exportar automáticamente todas las variables
while IFS='=' read -r key value; do
    # Ignorar líneas vacías y comentarios
    if [[ ! -z "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
        # Eliminar espacios en blanco alrededor del =
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Eliminar comillas si existen
        value="${value%\"}"
        value="${value#\"}"
        value="${value%\'}"
        value="${value#\'}"
        
        # Solo exportar si la variable tiene un valor
        if [ ! -z "$value" ]; then
            export "$key=$value"
        fi
    fi
done < "$ENV_FILE"
set +a

# Verificar que se cargaron las variables críticas
if [ -z "$PROJECT_ROOT" ]; then
    echo "⚠️  Advertencia: PROJECT_ROOT no está definido en .env"
    export PROJECT_ROOT="/home/mtg/api-dev"
fi

# Actualizar rutas derivadas
export SCRIPTS_PATH="${SCRIPTS_PATH:-$PROJECT_ROOT/scripts}"
export DATA_PATH="${DATA_PATH:-$PROJECT_ROOT/data}"
export PUERTOS_FILE="${PUERTOS_FILE:-$DATA_PATH/puertos_ocupados_odoo.txt}"
export DEV_INSTANCES_FILE="${DEV_INSTANCES_FILE:-$DATA_PATH/dev-instances.txt}"

# Mensaje de confirmación (solo si se ejecuta directamente)
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    echo "✅ Variables de entorno cargadas desde: $ENV_FILE"
    echo "   PROJECT_ROOT: $PROJECT_ROOT"
    echo "   DOMAIN_ROOT: $DOMAIN_ROOT"
    echo "   DB_USER: $DB_USER"
fi
