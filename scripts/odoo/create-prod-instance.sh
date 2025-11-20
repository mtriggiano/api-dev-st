#!/bin/bash

# 🚀 Router de creación de instancias Odoo en PRODUCCIÓN (Multi-Versión)
# Este script llama al script específico según la versión y edición seleccionada
# IMPORTANTE: Este script SIEMPRE crea instancias en SUBDOMINIOS
# NUNCA usa el dominio raíz para proteger el dominio principal
# Soporta: Odoo 19/18 Enterprise/Community

set -e

# Asegurar PATH completo
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Cargar utilidades
SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/odoo-version-manager.sh"

# Obtener parámetros
RAW_NAME="$1"
ODOO_VERSION="$2"  # Opcional: 19 o 18 (default: 19)
ODOO_EDITION="$3"  # Opcional: enterprise o community (default: enterprise)
SSL_METHOD="$4"   # Opcional: 1=letsencrypt, 2=cloudflare, 3=http

if [[ -z "$RAW_NAME" ]]; then 
    echo "❌ Debes pasar el nombre de la instancia (será usado como subdominio)."
    echo "   Ejemplo: ./create-prod-instance.sh cliente1 [version] [edition] [ssl_method]"
    echo "   Creará: cliente1.softrigx.com"
    echo ""
    echo "   Parámetros:"
    echo "   - version: 19 o 18 (default: 19)"
    echo "   - edition: enterprise o community (default: enterprise)"
    echo "   - ssl_method: 1=Let's Encrypt (default), 2=Cloudflare, 3=HTTP"
    echo ""
    list_odoo_versions
    exit 1
fi

# Valores por defecto
ODOO_VERSION="${ODOO_VERSION:-19}"
ODOO_EDITION="${ODOO_EDITION:-enterprise}"

# Validar versión de Odoo
if ! validate_odoo_version "$ODOO_VERSION" "$ODOO_EDITION"; then
    exit 1
fi

# Determinar qué script llamar
if [[ "$ODOO_EDITION" == "community" ]]; then
    EDITION_SUFFIX="c"
else
    EDITION_SUFFIX="e"
fi

TARGET_SCRIPT="$SCRIPT_DIR/init-production-${ODOO_VERSION}${EDITION_SUFFIX}.sh"

# Verificar que el script existe
if [[ ! -f "$TARGET_SCRIPT" ]]; then
    echo "❌ ERROR: Script no encontrado: $TARGET_SCRIPT"
    echo "   Versión solicitada: Odoo $ODOO_VERSION $(echo $ODOO_EDITION | tr '[:lower:]' '[:upper:]')"
    echo ""
    echo "📦 Scripts disponibles:"
    ls -1 "$SCRIPT_DIR"/init-production-*.sh 2>/dev/null | sed 's|.*/||' || echo "   Ninguno encontrado"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Creando instancia Odoo $ODOO_VERSION $(echo $ODOO_EDITION | tr '[:lower:]' '[:upper:]')"
echo "📝 Nombre: $RAW_NAME"
echo "📜 Script: $(basename $TARGET_SCRIPT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Llamar al script específico
exec "$TARGET_SCRIPT" "$RAW_NAME" "$SSL_METHOD"
