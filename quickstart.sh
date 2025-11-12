#!/bin/bash

# ========================================
# QUICKSTART - Configuración Inicial del Sistema API-DEV
# ========================================
# Este script configura el sistema para un nuevo entorno
# Genera el archivo .env con todas las configuraciones necesarias

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuración por defecto
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"

# ========================================
# FUNCIONES AUXILIARES
# ========================================

print_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_section() {
    echo ""
    echo -e "${YELLOW}► $1${NC}"
    echo -e "${CYAN}----------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Función para leer input con valor por defecto
read_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_password="$4"
    
    if [ -z "$default" ]; then
        echo -n -e "${WHITE}$prompt: ${NC}"
    else
        echo -n -e "${WHITE}$prompt ${CYAN}[$default]${NC}: "
    fi
    
    if [ "$is_password" == "true" ]; then
        read -s input
        echo ""  # Nueva línea después del password
    else
        read input
    fi
    
    if [ -z "$input" ]; then
        eval "$var_name='$default'"
    else
        eval "$var_name='$input'"
    fi
}

# Función para generar un secret aleatorio
generate_secret() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
    openssl rand -hex 32 2>/dev/null || \
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1
}

# Función para detectar IP pública
detect_public_ip() {
    curl -s ifconfig.me 2>/dev/null || \
    curl -s icanhazip.com 2>/dev/null || \
    curl -s ipinfo.io/ip 2>/dev/null || \
    echo ""
}

# Función para verificar comando
check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 está instalado"
        return 0
    else
        print_error "$1 NO está instalado"
        return 1
    fi
}

# Función para verificar conexión PostgreSQL
test_postgres_connection() {
    local user="$1"
    local pass="$2"
    local host="${3:-localhost}"
    local port="${4:-5432}"
    
    if PGPASSWORD="$pass" psql -h "$host" -p "$port" -U "$user" -d postgres -c '\q' 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Función para verificar Cloudflare API
test_cloudflare_api() {
    local token="$1"
    local zone="$2"
    
    local response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$zone" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q '"success":true'; then
        return 0
    else
        return 1
    fi
}

# ========================================
# INICIO DEL SCRIPT
# ========================================

clear

echo -e "${MAGENTA}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║           🚀 QUICKSTART - Sistema API-DEV 🚀             ║"
echo "║                                                           ║"
echo "║         Configuración Inicial para Nuevo Entorno         ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_info "Este script configurará el sistema para un nuevo entorno"
print_info "Se creará el archivo .env con todas las configuraciones necesarias"

# Verificar si ya existe un .env
if [ -f "$ENV_FILE" ]; then
    print_warning "Ya existe un archivo .env"
    echo -e "${YELLOW}¿Deseas sobrescribirlo? Esto eliminará la configuración actual.${NC}"
    read_with_default "Continuar? (s/n)" "n" OVERWRITE
    
    if [ "$OVERWRITE" != "s" ] && [ "$OVERWRITE" != "S" ]; then
        print_info "Operación cancelada. El archivo .env existente no fue modificado."
        exit 0
    fi
    
    # Hacer backup del .env actual
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "Backup creado: $ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# ========================================
# PASO 1: VERIFICACIÓN DE DEPENDENCIAS
# ========================================

print_header "PASO 1: Verificación de Dependencias"

DEPS_OK=true

check_command "python3" || DEPS_OK=false
check_command "psql" || DEPS_OK=false
check_command "nginx" || DEPS_OK=false
check_command "git" || DEPS_OK=false
check_command "curl" || DEPS_OK=false
check_command "jq" || DEPS_OK=false
check_command "node" || DEPS_OK=false
check_command "npm" || DEPS_OK=false

# Verificación especial para Git en /usr/bin/git (requerido para integración GitHub)
if [ -f "/usr/bin/git" ]; then
    print_success "Git está en /usr/bin/git (requerido para integración GitHub)"
else
    print_warning "Git NO está en /usr/bin/git"
    print_info "La integración GitHub requiere Git en /usr/bin/git"
    if command -v git &> /dev/null; then
        GIT_PATH=$(which git)
        print_info "Git encontrado en: $GIT_PATH"
        print_info "Puedes crear un symlink: sudo ln -s $GIT_PATH /usr/bin/git"
    fi
fi

if [ "$DEPS_OK" = false ]; then
    print_error "Faltan dependencias necesarias"
    echo ""
    echo "Para instalarlas en Ubuntu/Debian:"
    echo "sudo apt update"
    echo "sudo apt install -y python3 python3-pip postgresql-client nginx git curl jq"
    echo "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
    echo "sudo apt install -y nodejs"
    echo ""
    read_with_default "¿Continuar de todos modos? (s/n)" "n" CONTINUE
    
    if [ "$CONTINUE" != "s" ] && [ "$CONTINUE" != "S" ]; then
        exit 1
    fi
fi

# ========================================
# PASO 2: INFORMACIÓN DEL SISTEMA
# ========================================

print_header "PASO 2: Información del Sistema"

# Usuario del sistema
CURRENT_USER=$(whoami)
print_info "Usuario actual del sistema: $CURRENT_USER"
read_with_default "Usuario del sistema para los servicios" "$CURRENT_USER" SYSTEM_USER

# Detectar IP pública
print_info "Detectando IP pública..."
DETECTED_IP=$(detect_public_ip)
if [ ! -z "$DETECTED_IP" ]; then
    print_success "IP pública detectada: $DETECTED_IP"
else
    print_warning "No se pudo detectar la IP pública automáticamente"
fi
read_with_default "IP pública del servidor" "$DETECTED_IP" PUBLIC_IP

# ========================================
# PASO 3: CONFIGURACIÓN DE DOMINIO
# ========================================

print_header "PASO 3: Configuración de Dominio"

read_with_default "Dominio raíz (ej: miempresa.com)" "hospitalprivadosalta.ar" DOMAIN_ROOT
read_with_default "Subdominio para el panel (ej: api-dev)" "api-dev" API_SUBDOMAIN

API_DOMAIN="$API_SUBDOMAIN.$DOMAIN_ROOT"
print_info "URL del panel será: https://$API_DOMAIN"

# ========================================
# PASO 4: CLOUDFLARE API
# ========================================

print_header "PASO 4: Configuración de Cloudflare"

print_info "Se necesita un token de Cloudflare con permisos de Zone:Edit"
print_info "Puedes crearlo en: https://dash.cloudflare.com/profile/api-tokens"

read_with_default "Token de API de Cloudflare" "" CF_API_TOKEN
read_with_default "Email de Cloudflare" "admin@$DOMAIN_ROOT" CF_EMAIL

# Verificar Cloudflare
if [ ! -z "$CF_API_TOKEN" ]; then
    print_info "Verificando conexión con Cloudflare..."
    if test_cloudflare_api "$CF_API_TOKEN" "$DOMAIN_ROOT"; then
        print_success "Conexión con Cloudflare exitosa"
    else
        print_warning "No se pudo verificar la conexión con Cloudflare"
        print_info "Verifica que el token tenga los permisos correctos"
    fi
fi

# ========================================
# PASO 5: POSTGRESQL
# ========================================

print_header "PASO 5: Configuración de PostgreSQL"

read_with_default "Usuario de PostgreSQL" "go" DB_USER
read_with_default "Contraseña de PostgreSQL" "" DB_PASSWORD true
read_with_default "Host de PostgreSQL" "localhost" DB_HOST
read_with_default "Puerto de PostgreSQL" "5432" DB_PORT

# Verificar conexión
print_info "Verificando conexión con PostgreSQL..."
if test_postgres_connection "$DB_USER" "$DB_PASSWORD" "$DB_HOST" "$DB_PORT"; then
    print_success "Conexión con PostgreSQL exitosa"
else
    print_warning "No se pudo conectar a PostgreSQL"
    print_info "Verifica las credenciales y que el servicio esté activo"
fi

# ========================================
# PASO 6: CONFIGURACIÓN DE ODOO
# ========================================

print_header "PASO 6: Configuración de Odoo"

# Detectar si existe una instancia con nombre diferente
EXISTING_INSTANCE=""
if [ -d "/home/go/apps/production/odoo" ]; then
    for dir in /home/go/apps/production/odoo/*/; do
        if [ -d "$dir" ]; then
            EXISTING_INSTANCE=$(basename "$dir")
            break
        fi
    done
fi

if [ ! -z "$EXISTING_INSTANCE" ] && [ "$EXISTING_INSTANCE" != "odoo-production" ]; then
    print_warning "Se detectó una instancia existente: '$EXISTING_INSTANCE'"
    echo ""
    echo "1) Usar '$EXISTING_INSTANCE' como instancia de producción"
    echo "2) Usar 'odoo-production' (recomendado para nuevas instalaciones)"
    echo "3) Especificar otro nombre"
    echo ""
    read_with_default "Selección (1/2/3)" "2" INSTANCE_CHOICE
    
    case $INSTANCE_CHOICE in
        1)
            PROD_INSTANCE_NAME="$EXISTING_INSTANCE"
            ;;
        2)
            PROD_INSTANCE_NAME="odoo-production"
            ;;
        3)
            read_with_default "Nombre de la instancia de producción" "odoo-production" PROD_INSTANCE_NAME
            ;;
        *)
            PROD_INSTANCE_NAME="odoo-production"
            ;;
    esac
else
    read_with_default "Nombre de la instancia de producción" "odoo-production" PROD_INSTANCE_NAME
fi

read_with_default "Contraseña de administrador de Odoo" "$DB_PASSWORD" ODOO_ADMIN_PASSWORD true
read_with_default "Ruta del repositorio Odoo (ZIP)" "/home/go/apps/repo/odoo19e.zip" ODOO_REPO_PATH

# Verificar si existe el archivo ZIP
if [ -f "$ODOO_REPO_PATH" ]; then
    print_success "Archivo del repositorio encontrado"
else
    print_warning "El archivo del repositorio no existe en: $ODOO_REPO_PATH"
    print_info "Será necesario para crear nuevas instancias"
fi

# ========================================
# PASO 7: RUTAS DEL SISTEMA
# ========================================

print_header "PASO 7: Rutas del Sistema"

read_with_default "Ruta de instancias de producción" "/home/go/apps/production/odoo" PROD_ROOT
read_with_default "Ruta de instancias de desarrollo" "/home/go/apps/develop/odoo" DEV_ROOT
read_with_default "Ruta de backups" "/home/go/backups" BACKUPS_PATH
read_with_default "Binario de Python" "/usr/bin/python3.12" PYTHON_BIN

# Verificar Python
if [ -f "$PYTHON_BIN" ]; then
    PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
    print_success "Python encontrado: $PYTHON_VERSION"
else
    print_warning "El binario de Python no existe en: $PYTHON_BIN"
fi

# ========================================
# PASO 8: CONFIGURACIÓN DEL PANEL
# ========================================

print_header "PASO 8: Configuración del Panel de Control"

print_info "Generando secrets para Flask y JWT..."
SECRET_KEY=$(generate_secret)
JWT_SECRET_KEY=$(generate_secret)
print_success "Secrets generados automáticamente"

read_with_default "Nombre de la base de datos del panel" "server_panel" DB_NAME_PANEL
read_with_default "Modo de Flask (development/production)" "production" FLASK_ENV
read_with_default "Nivel de log (debug/info/warning/error)" "info" LOG_LEVEL
read_with_default "Retención de backups (días)" "7" BACKUP_RETENTION_DAYS

# ========================================
# PASO 9: GENERACIÓN DEL ARCHIVO .ENV
# ========================================

print_header "PASO 9: Generando Archivo de Configuración"

cat > "$ENV_FILE" << EOF
# ========================================
# CONFIGURACIÓN DEL SISTEMA API-DEV
# ========================================
# Archivo generado automáticamente por quickstart.sh
# Fecha: $(date)

# ========================================
# CONFIGURACIÓN DEL SISTEMA OPERATIVO
# ========================================
SYSTEM_USER=$SYSTEM_USER

# ========================================
# POSTGRESQL - Base de Datos
# ========================================
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT

# ========================================
# CLOUDFLARE - Gestión de DNS
# ========================================
CF_API_TOKEN=$CF_API_TOKEN
CF_ZONE_NAME=$DOMAIN_ROOT
CF_EMAIL=$CF_EMAIL

# ========================================
# SERVIDOR - Configuración de Red
# ========================================
PUBLIC_IP=$PUBLIC_IP
DOMAIN_ROOT=$DOMAIN_ROOT

# ========================================
# ODOO - Configuración de Instancias
# ========================================
ODOO_ADMIN_PASSWORD=$ODOO_ADMIN_PASSWORD
PROD_INSTANCE_NAME=$PROD_INSTANCE_NAME
PROD_ROOT=$PROD_ROOT
DEV_ROOT=$DEV_ROOT
ODOO_REPO_PATH=$ODOO_REPO_PATH
PYTHON_BIN=$PYTHON_BIN

# ========================================
# PANEL DE CONTROL (API-DEV)
# ========================================
API_DOMAIN=$API_DOMAIN
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
DB_NAME_PANEL=$DB_NAME_PANEL

# ========================================
# RUTAS DEL SISTEMA
# ========================================
PROJECT_ROOT=$PROJECT_ROOT
SCRIPTS_PATH=$PROJECT_ROOT/scripts
DATA_PATH=$PROJECT_ROOT/data
PUERTOS_FILE=$PROJECT_ROOT/data/puertos_ocupados_odoo.txt
DEV_INSTANCES_FILE=$PROJECT_ROOT/data/dev-instances.txt
BACKUPS_PATH=$BACKUPS_PATH

# ========================================
# CONFIGURACIÓN ADICIONAL
# ========================================
FLASK_ENV=$FLASK_ENV
LOG_LEVEL=$LOG_LEVEL
BACKUP_RETENTION_DAYS=$BACKUP_RETENTION_DAYS
EOF

# Establecer permisos seguros
chmod 600 "$ENV_FILE"
print_success "Archivo .env creado con permisos seguros (600)"

# ========================================
# PASO 10: INICIALIZACIÓN DEL SISTEMA
# ========================================

print_header "PASO 10: Inicialización del Sistema"

# Crear estructura de directorios si no existe
print_info "Creando estructura de directorios..."
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/config"
mkdir -p "$BACKUPS_PATH"

# Crear archivos de datos si no existen
touch "$PROJECT_ROOT/data/puertos_ocupados_odoo.txt"
touch "$PROJECT_ROOT/data/dev-instances.txt"
print_success "Estructura de directorios creada"

# Hacer ejecutables los scripts
print_info "Configurando permisos de scripts..."
chmod +x "$PROJECT_ROOT/scripts/utils/"*.sh 2>/dev/null || true
chmod +x "$PROJECT_ROOT/scripts/odoo/"*.sh 2>/dev/null || true
print_success "Permisos configurados"

# ========================================
# RESUMEN FINAL
# ========================================

print_header "✨ CONFIGURACIÓN COMPLETADA ✨"

echo ""
echo -e "${GREEN}El sistema ha sido configurado exitosamente.${NC}"
echo ""
echo -e "${WHITE}Resumen de la configuración:${NC}"
echo -e "${CYAN}----------------------------------------${NC}"
echo -e "📁 Proyecto: ${WHITE}$PROJECT_ROOT${NC}"
echo -e "🌐 Dominio: ${WHITE}$DOMAIN_ROOT${NC}"
echo -e "🖥️  Panel: ${WHITE}https://$API_DOMAIN${NC}"
echo -e "👤 Usuario: ${WHITE}$SYSTEM_USER${NC}"
echo -e "🗄️  PostgreSQL: ${WHITE}$DB_USER@$DB_HOST:$DB_PORT${NC}"
echo -e "🏭 Instancia Producción: ${WHITE}$PROD_INSTANCE_NAME${NC}"
echo -e "${CYAN}----------------------------------------${NC}"

echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo ""
echo "1. Verificar la configuración:"
echo -e "   ${CYAN}source scripts/utils/validate-env.sh --full${NC}"
echo ""
echo "2. Desplegar el panel de control:"
echo -e "   ${CYAN}./deploy.sh${NC}"
echo ""
echo "3. Crear instancia de producción (si no existe):"
echo -e "   ${CYAN}./scripts/odoo/init-production.sh${NC}"
echo ""
echo "4. Crear instancia de desarrollo:"
echo -e "   ${CYAN}./scripts/odoo/create-dev-instance.sh nombre-dev${NC}"
echo ""

print_success "¡El sistema está listo para usar!"
echo ""

# Preguntar si desea ejecutar validación completa
read_with_default "¿Deseas ejecutar la validación completa ahora? (s/n)" "s" RUN_VALIDATION

if [ "$RUN_VALIDATION" == "s" ] || [ "$RUN_VALIDATION" == "S" ]; then
    echo ""
    source "$PROJECT_ROOT/scripts/utils/load-env.sh"
    source "$PROJECT_ROOT/scripts/utils/validate-env.sh" --full
fi

echo ""
print_info "Archivo de configuración guardado en: $ENV_FILE"
print_info "Puedes editar manualmente este archivo si necesitas cambiar algún valor"
echo ""
