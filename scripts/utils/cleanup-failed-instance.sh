#!/bin/bash
# Script para limpiar instancias de desarrollo fallidas

set -e

INSTANCE_NAME="$1"

if [[ -z "$INSTANCE_NAME" ]]; then
    echo "❌ Debes proporcionar el nombre de la instancia a limpiar"
    echo "   Uso: $0 <nombre-instancia>"
    echo "   Ejemplo: $0 dev-mtg"
    exit 1
fi

echo "🧹 Limpiando instancia fallida: $INSTANCE_NAME"
echo ""

# Detectar tipo de instancia
if [[ "$INSTANCE_NAME" == dev-* ]]; then
    INSTANCE_TYPE="development"
    BASE_DIR="/home/mtg/apps/develop/odoo"
    TRACKING_FILE="/home/mtg/api-dev/data/dev-instances.txt"
elif [[ "$INSTANCE_NAME" == prod-* ]]; then
    INSTANCE_TYPE="production"
    BASE_DIR="/home/mtg/apps/production/odoo"
    TRACKING_FILE="/home/mtg/api-dev/data/prod-instances.txt"
else
    echo "❌ Nombre de instancia inválido. Debe empezar con 'dev-' o 'prod-'"
    exit 1
fi

echo "📋 Tipo: $INSTANCE_TYPE"
echo "📁 Directorio: $BASE_DIR/$INSTANCE_NAME"
echo ""

# Confirmar
read -p "¿Estás seguro de eliminar esta instancia? (s/N): " confirm
if [[ "$confirm" != "s" ]] && [[ "$confirm" != "S" ]]; then
    echo "❌ Operación cancelada"
    exit 0
fi

echo ""
echo "🗑️  Eliminando componentes..."

# 1. Detener y eliminar servicio
SERVICE_NAME="odoo19e-$INSTANCE_NAME"
if systemctl list-units --full --all | grep -q "$SERVICE_NAME"; then
    echo "  ⏹️  Deteniendo servicio $SERVICE_NAME..."
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    echo "  ✅ Servicio eliminado"
else
    echo "  ℹ️  No hay servicio systemd"
fi

# 2. Buscar y eliminar base de datos
echo "  🗄️  Buscando bases de datos..."
DBS=$(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE datname LIKE '%$INSTANCE_NAME%' OR datname LIKE '%${INSTANCE_NAME#dev-}%' OR datname LIKE '%${INSTANCE_NAME#prod-}%';" | grep -v '^\s*$' | xargs)

if [[ -n "$DBS" ]]; then
    for db in $DBS; do
        echo "  🗑️  Eliminando BD: $db"
        sudo -u postgres dropdb "$db" 2>/dev/null || true
    done
    echo "  ✅ Bases de datos eliminadas"
else
    echo "  ℹ️  No hay bases de datos"
fi

# 3. Eliminar directorio
if [[ -d "$BASE_DIR/$INSTANCE_NAME" ]]; then
    echo "  📁 Eliminando directorio..."
    rm -rf "$BASE_DIR/$INSTANCE_NAME"
    echo "  ✅ Directorio eliminado"
else
    echo "  ℹ️  No hay directorio"
fi

# 4. Eliminar configuración nginx
if [[ -f "/etc/nginx/sites-enabled/$INSTANCE_NAME" ]] || [[ -f "/etc/nginx/sites-available/$INSTANCE_NAME" ]]; then
    echo "  🌐 Eliminando configuración nginx..."
    sudo rm -f "/etc/nginx/sites-enabled/$INSTANCE_NAME"
    sudo rm -f "/etc/nginx/sites-available/$INSTANCE_NAME"
    echo "  ✅ Configuración nginx eliminada"
else
    echo "  ℹ️  No hay configuración nginx"
fi

# 5. Eliminar del tracking
if [[ -f "$TRACKING_FILE" ]]; then
    echo "  📝 Eliminando del tracking..."
    sed -i "/$INSTANCE_NAME/d" "$TRACKING_FILE" 2>/dev/null || true
    echo "  ✅ Tracking actualizado"
fi

# 6. Recargar servicios
echo "  🔄 Recargando servicios..."
sudo systemctl daemon-reload
if sudo nginx -t 2>/dev/null; then
    sudo systemctl reload nginx 2>/dev/null || true
    echo "  ✅ Servicios recargados"
else
    echo "  ⚠️  Error en configuración nginx (puede ser normal)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Instancia $INSTANCE_NAME limpiada exitosamente"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Ahora puedes crear la instancia nuevamente desde el panel web"
