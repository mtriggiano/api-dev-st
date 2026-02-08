#!/bin/bash

# ========================================
# UPDATE - Script de Actualización API-DEV
# ========================================
# Este script actualiza una instalación existente de API-DEV
# NO usar en instalaciones nuevas (usar quickstart.sh)

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="/tmp/api-dev-backup-$(date +%Y%m%d_%H%M%S)"

UPDATE_MODE="github"
NON_INTERACTIVE=false
if [ "$1" = "--local" ] || [ "$1" = "local" ] || [ "$1" = "--no-pull" ]; then
    UPDATE_MODE="local"
elif [ "$1" = "--github" ] || [ "$1" = "github" ] || [ -z "$1" ]; then
    UPDATE_MODE="github"
else
    echo "Uso: $0 [--github|--local]"
    exit 1
fi

if [ "$2" = "--non-interactive" ] || [ "$2" = "--yes" ] || [ "$2" = "-y" ]; then
    NON_INTERACTIVE=true
fi

# Cargar variables del .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck source=/dev/null
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# Configuración
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Cargar variables del .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | grep -v '^[[:space:]]*$' | xargs)
    print_info() { echo -e "\033[0;34mℹ️  $1\033[0m"; }
    print_info "Variables cargadas desde .env"
fi

# Usar BACKUPS_PATH del .env o fallback a /tmp
BACKUP_DIR="${BACKUPS_PATH:-/tmp}/api-dev-backup-$(date +%Y%m%d_%H%M%S)"

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

fix_odoo_nginx() {
    local SCRIPTS_DIR="${SCRIPTS_PATH:-$PROJECT_ROOT/scripts}"
    if [ ! -f "$SCRIPTS_DIR/utils/ssl-manager.sh" ]; then
        print_error "ssl-manager.sh no encontrado en $SCRIPTS_DIR/utils"
        return 1
    fi
    # shellcheck source=/dev/null
    source "$SCRIPTS_DIR/utils/ssl-manager.sh"

    read -p "Dominio Odoo a corregir (ej: ejemplo.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        print_error "Dominio vacío"
        return 1
    fi

    local DEFAULT_CONF="${PROD_ROOT}/production/odoo.conf"
    read -p "Ruta a odoo.conf [$DEFAULT_CONF]: " ODOO_CONF
    ODOO_CONF=${ODOO_CONF:-$DEFAULT_CONF}
    if [ ! -f "$ODOO_CONF" ]; then
        print_error "No existe $ODOO_CONF"
        return 1
    fi

    local PORT EVENTED_PORT INSTANCE_NAME CERT_FILE KEY_FILE
    PORT=$(awk -F'=' '/^[[:space:]]*http_port[[:space:]]*=/{gsub(/[[:space:]]/,"",$2); print $2}' "$ODOO_CONF")
    EVENTED_PORT=$(awk -F'=' '/^[[:space:]]*gevent_port[[:space:]]*=/{gsub(/[[:space:]]/,"",$2); print $2}' "$ODOO_CONF")
    if [ -z "$PORT" ]; then
        read -p "http_port no encontrado. Ingresar puerto HTTP: " PORT
    fi
    if [ -z "$EVENTED_PORT" ]; then
        read -p "gevent_port no encontrado. Ingresar EVENTED_PORT [8072]: " EVENTED_PORT
        EVENTED_PORT=${EVENTED_PORT:-8072}
    fi
    INSTANCE_NAME=$(basename "$(dirname "$ODOO_CONF")")

    CERT_FILE="/etc/ssl/cloudflare/$DOMAIN.crt"
    KEY_FILE="/etc/ssl/cloudflare/$DOMAIN.key"

    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        print_info "Usando Let's Encrypt existente"
        configure_nginx_letsencrypt_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$EVENTED_PORT"
    elif [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        print_info "Usando Cloudflare Origin existente"
        configure_nginx_cloudflare_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$CERT_FILE" "$KEY_FILE" "$EVENTED_PORT"
    else
        print_warning "Sin certificado encontrado. Configurando HTTP"
        configure_http_only "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$EVENTED_PORT"
    fi

    sudo nginx -t && sudo systemctl reload nginx
    print_success "Nginx corregido para $DOMAIN (EVENTED_PORT=$EVENTED_PORT)"
}

# ========================================
# VERIFICACIONES PREVIAS
# ========================================

print_header "API-DEV - Script de Actualización"

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    print_error "No se encontró el archivo .env"
    print_info "Este script debe ejecutarse desde el directorio raíz de API-DEV"
    exit 1
fi

# Verificar que el servicio existe
if ! systemctl list-unit-files | grep -q "server-panel-api.service"; then
    print_error "El servicio server-panel-api no está instalado"
    print_info "Este script es solo para actualizar instalaciones existentes"
    exit 1
fi

print_success "Instalación existente detectada"

# ========================================
# PASO 1: BACKUP DE SEGURIDAD
# ========================================

print_header "PASO 1: Backup de Seguridad"

mkdir -p "$BACKUP_DIR"

# Backup del .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    cp "$PROJECT_ROOT/.env" "$BACKUP_DIR/.env"
    print_success "Backup de .env creado"
fi

# Backup de la base de datos
print_info "Creando backup de la base de datos..."
if [ ! -z "$DB_NAME_PANEL" ]; then
    pg_dump "$DB_NAME_PANEL" > "$BACKUP_DIR/database.sql" 2>/dev/null || print_warning "No se pudo hacer backup de la BD"
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        print_success "Backup de base de datos creado"
    fi
fi

print_info "Backups guardados en: $BACKUP_DIR"

# ========================================
# PASO 2: OBTENER CAMBIOS DE GIT
# ========================================

print_header "PASO 2: Actualizar Código desde Git"

cd "$PROJECT_ROOT"

# Guardar commit actual para detectar cambios post-pull
PREV_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
print_info "Commit local antes de actualizar: $PREV_HEAD"

if [ "$UPDATE_MODE" = "github" ]; then
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "Hay cambios locales sin commitear"
        echo ""
        git status --short
        echo ""
        read -p "¿Descartar cambios locales y continuar? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            git reset --hard
            print_info "Cambios locales descartados"
        else
            print_error "Actualización cancelada"
            exit 1
        fi
    fi
else
    if [ -n "$(git status --porcelain)" ]; then
        print_info "Modo local: se conservarán los cambios locales"
        echo ""
        git status --short
        echo ""
    fi
fi

# Obtener rama actual
CURRENT_BRANCH=$(git branch --show-current)
print_info "Rama actual: $CURRENT_BRANCH"

if [ "$UPDATE_MODE" = "github" ]; then
    print_info "Descargando cambios..."
    if git pull origin "$CURRENT_BRANCH"; then
        print_success "Código actualizado desde Git"
    else
        print_error "Error al hacer pull desde Git"
        exit 1
    fi
else
    print_info "Modo local: no se descargan cambios desde Git"
fi

NEW_HEAD=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
print_info "Commit local después de actualizar: $NEW_HEAD"

# Mostrar últimos commits
echo ""
print_info "Últimos cambios:"
git log --oneline -5 --color=always

# ========================================
# PASO 3: ACTUALIZAR BACKEND
# ========================================

print_header "PASO 3: Actualizar Backend"

cd "$PROJECT_ROOT/backend"

# Activar entorno virtual
if [ -d "venv" ]; then
    print_info "Activando entorno virtual..."
    source venv/bin/activate
    print_success "Entorno virtual activado"
else
    print_error "No se encontró el entorno virtual"
    exit 1
fi

# Actualizar dependencias
print_info "Actualizando dependencias de Python..."
if pip install -r requirements.txt --quiet; then
    print_success "Dependencias de Python actualizadas"
else
    print_warning "Algunas dependencias no se pudieron actualizar"
fi

# Verificar si hay migraciones nuevas
print_section "Verificando Migraciones"

if [ -d "migrations" ]; then
    MIGRATIONS=$(find migrations -name "*.py" -type f ! -name "__*")
    if [ ! -z "$MIGRATIONS" ]; then
        print_info "Migraciones encontradas:"
        echo "$MIGRATIONS" | while read migration; do
            echo "  - $(basename $migration)"
        done
        echo ""
        if [ "$NON_INTERACTIVE" = true ]; then
            print_warning "Modo no interactivo: migraciones omitidas"
        else
            read -p "¿Ejecutar migraciones? (s/n): " -n 1 -r
            echo
        fi
        if [ "$NON_INTERACTIVE" = false ] && [[ $REPLY =~ ^[Ss]$ ]]; then
            echo "$MIGRATIONS" | while read migration; do
                print_info "Ejecutando: $(basename $migration)"
                if python "$migration"; then
                    print_success "Migración completada: $(basename $migration)"
                else
                    print_error "Error en migración: $(basename $migration)"
                fi
            done
        else
            print_warning "Migraciones omitidas"
        fi
    else
        print_info "No hay migraciones pendientes"
    fi
fi

# ========================================
# PASO 4: ACTUALIZAR FRONTEND
# ========================================

print_header "PASO 4: Actualizar Frontend"

cd "$PROJECT_ROOT/frontend"

# Verificar si hay cambios en package.json
PKG_CHANGED=false
if [ "$UPDATE_MODE" = "github" ]; then
    if [ "$PREV_HEAD" != "unknown" ] && [ "$NEW_HEAD" != "unknown" ] && ! git diff --quiet "$PREV_HEAD" "$NEW_HEAD" -- package.json; then
        PKG_CHANGED=true
    fi
else
    if ! git diff --quiet -- package.json; then
        PKG_CHANGED=true
    fi
fi

if [ "$PKG_CHANGED" = true ]; then
    print_info "Detectados cambios en dependencias del frontend"
    print_info "Instalando dependencias de Node.js..."
    if npm install; then
        print_success "Dependencias de Node.js actualizadas"
    else
        print_warning "Algunas dependencias no se pudieron actualizar"
    fi
else
    print_info "No hay cambios en dependencias del frontend"
fi

# Construir frontend
print_info "Construyendo frontend..."
if npm run build; then
    print_success "Frontend construido exitosamente"
else
    print_error "Error al construir el frontend"
    exit 1
fi

# ========================================
# PASO 5: REINICIAR SERVICIOS
# ========================================

print_header "PASO 5: Reiniciar Servicios"

# Reiniciar servicio backend
print_info "Reiniciando servicio backend..."
if sudo systemctl restart server-panel-api; then
    print_success "Servicio backend reiniciado"
else
    print_error "Error al reiniciar servicio backend"
    exit 1
fi

# Esperar a que el servicio esté activo
sleep 3

# Verificar estado del servicio
if systemctl is-active --quiet server-panel-api; then
    print_success "Servicio backend está activo"
else
    print_error "El servicio backend no está activo"
    print_info "Ver logs: sudo journalctl -u server-panel-api -n 50"
    exit 1
fi

# Recargar Nginx (opcional)
if systemctl is-active --quiet nginx; then
    print_info "Recargando configuración de Nginx..."
    if sudo systemctl reload nginx; then
        print_success "Nginx recargado"
    fi
fi

# Si hay un frontend en modo dev (Vite) corriendo, reiniciarlo para que tome cambios
if pgrep -f "npm.*dev" > /dev/null 2>&1; then
    print_info "Detectado frontend en modo dev (Vite). Reiniciando para aplicar cambios..."
    if "$PROJECT_ROOT/scripts/utils/restart-services.sh" frontend; then
        print_success "Frontend dev reiniciado"
    else
        print_warning "No se pudo reiniciar el frontend dev"
    fi
else
    print_info "Frontend dev (Vite) no detectado. Si estás usando http://localhost:5173, reiniciá con: $PROJECT_ROOT/restart.sh"
fi

# ========================================
# PASO 6: VERIFICACIONES POST-ACTUALIZACIÓN
# ========================================

print_header "PASO 6: Verificaciones"

# Verificar API
print_info "Verificando API..."
sleep 2

if [ ! -z "$API_DOMAIN" ]; then
    if curl -s -o /dev/null -w "%{http_code}" "https://$API_DOMAIN/api/health" | grep -q "200"; then
        print_success "API respondiendo correctamente"
    else
        print_warning "API no responde en https://$API_DOMAIN/api/health"
    fi
fi

# Verificar logs recientes
print_section "Últimos Logs del Servicio"
sudo journalctl -u server-panel-api -n 10 --no-pager

print_section "Estado del Servicio Cron"
if systemctl is-active --quiet cron 2>/dev/null; then
    print_success "Servicio cron está activo"
elif systemctl is-active --quiet crond 2>/dev/null; then
    print_success "Servicio crond está activo"
else
    print_warning "Servicio cron no está activo"
    print_info "Los backups automáticos requieren cron activo"
fi

# ========================================
# RESUMEN FINAL
# ========================================

print_header "Actualización Completada"

echo ""
print_success "✅ Código actualizado desde Git"
print_success "✅ Dependencias actualizadas"
print_success "✅ Frontend reconstruido"
print_success "✅ Servicios reiniciados"
echo ""

print_info "🔖 Commit desplegado: $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
print_info "🕒 Último commit: $(git log -1 --oneline 2>/dev/null || echo unknown)"

print_info "📦 Backup guardado en: $BACKUP_DIR"
echo ""

print_section "Próximos Pasos"
echo "1. Verificar que el panel funciona correctamente"
echo "2. Revisar logs si hay algún problema:"
echo "   sudo journalctl -u server-panel-api -f"
echo ""
echo "3. Si algo falla, puedes restaurar el backup:"
echo "   cp $BACKUP_DIR/.env $PROJECT_ROOT/.env"
echo "   psql $DB_NAME_PANEL < $BACKUP_DIR/database.sql"
echo "   sudo systemctl restart server-panel-api"
echo ""

if [ "$NON_INTERACTIVE" = true ]; then
    print_info "Modo no interactivo: omitida corrección de Nginx"
else
    read -p "¿Corregir ahora la configuración de Nginx para una instancia de Odoo en este servidor? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        fix_odoo_nginx || print_error "No se pudo corregir Nginx de Odoo"
    fi
fi

print_section "Nuevas Funcionalidades en esta Versión"
echo "• Monitoreo de servicio cron en panel de Backups"
echo "• Visualización de commit actual en instancias"
echo "• Logs de Git/Deploy en panel de instancias"
echo "• Webhooks de GitHub para auto-deploy"
echo "• Correcciones en rutas absolutas para crontab"
echo ""

print_success "🎉 ¡Actualización completada exitosamente!"
echo ""