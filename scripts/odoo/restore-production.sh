#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 🔄 Script de restauración de backup de producción Odoo
# Compatible con formato estándar de Odoo Online
# Incluye backup de seguridad antes de restaurar

set -e

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"

# Configuración desde .env
PROD_INSTANCE="${PROD_INSTANCE_NAME:-odoo-production}"
PROD_DB="${PROD_INSTANCE_NAME:-odoo-production}"
BACKUP_DIR="${BACKUPS_PATH:-/home/mtg/backups}"
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
PROD_FILESTORE="$FILESTORE_BASE/$PROD_DB"
USER="${SYSTEM_USER:-go}"

# Detectar automáticamente el servicio (odoo19e o odoo18e)
# Buscar cualquier servicio odoo que exista (principal, production, etc.)
SERVICE_NAME=""
for service_file in /etc/systemd/system/odoo*.service; do
    if [[ -f "$service_file" ]]; then
        # Extraer el nombre del servicio sin la extensión .service
        SERVICE_NAME=$(basename "$service_file" .service)
        if [[ "$SERVICE_NAME" =~ ^odoo19e- ]]; then
            echo "🔍 Detectado: Odoo 19 Enterprise - Servicio: $SERVICE_NAME"
            break
        elif [[ "$SERVICE_NAME" =~ ^odoo18e- ]]; then
            echo "🔍 Detectado: Odoo 18 Enterprise - Servicio: $SERVICE_NAME"
            break
        elif [[ "$SERVICE_NAME" =~ ^odoo18- ]]; then
            echo "🔍 Detectado: Odoo 18 Community - Servicio: $SERVICE_NAME"
            break
        fi
    fi
done

if [[ -z "$SERVICE_NAME" ]]; then
    echo "❌ Error: No se encontró ningún servicio systemd de Odoo"
    echo "   Buscado en: /etc/systemd/system/odoo*.service"
    echo "   Servicios disponibles:"
    ls -1 /etc/systemd/system/odoo*.service 2>/dev/null || echo "   (ninguno)"
    exit 1
fi

# Validar argumentos
if [ $# -ne 1 ]; then
    echo "❌ Error: Se requiere el nombre del archivo de backup"
    echo "Uso: $0 <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

# Validar que el archivo existe
if [ ! -f "$BACKUP_PATH" ]; then
    echo "❌ Error: El archivo de backup no existe: $BACKUP_PATH"
    exit 1
fi

# Validar formato del archivo
if [[ ! "$BACKUP_FILE" =~ \.tar\.gz$ ]]; then
    echo "❌ Error: El archivo debe ser un .tar.gz"
    exit 1
fi

echo "🔄 ============================================"
echo "   RESTAURACIÓN DE BACKUP DE PRODUCCIÓN"
echo "============================================"
echo ""
echo "⚠️  ADVERTENCIA: Esta operación:"
echo "   • Detendrá el servicio de Odoo"
echo "   • Creará un backup de seguridad actual"
echo "   • Reemplazará la base de datos actual"
echo "   • Reemplazará el filestore actual"
echo ""
echo "📦 Backup a restaurar: $BACKUP_FILE"
echo "🗄️  Base de datos: $PROD_DB"
echo "📁 Filestore: $PROD_FILESTORE"
echo "🔧 Servicio: $SERVICE_NAME"
echo ""

# Directorio temporal para extracción
TEMP_DIR="/tmp/odoo_restore_$$"
SAFETY_BACKUP_DIR="/tmp/odoo_safety_backup_$$"

# Función de limpieza
cleanup() {
    echo "🧹 Limpiando archivos temporales..."
    rm -rf "$TEMP_DIR" 2>/dev/null || true
}

# Función de rollback
rollback() {
    echo ""
    echo "❌ ============================================"
    echo "   ERROR EN LA RESTAURACIÓN"
    echo "============================================"
    echo ""
    echo "🔄 Iniciando rollback al estado anterior..."
    
    if [ -d "$SAFETY_BACKUP_DIR" ]; then
        # Restaurar base de datos
        if [ -f "$SAFETY_BACKUP_DIR/dump.sql" ]; then
            echo "🗄️  Restaurando base de datos anterior..."
            sudo -u postgres dropdb --if-exists "$PROD_DB" 2>/dev/null || true
            sudo -u postgres createdb -O "$USER" "$PROD_DB"
            sudo -u postgres psql -d "$PROD_DB" < "$SAFETY_BACKUP_DIR/dump.sql" > /dev/null 2>&1
            echo "✅ Base de datos restaurada"
        fi
        
        # Restaurar filestore
        if [ -d "$SAFETY_BACKUP_DIR/filestore" ]; then
            echo "📁 Restaurando filestore anterior..."
            rm -rf "$PROD_FILESTORE"
            cp -r "$SAFETY_BACKUP_DIR/filestore" "$PROD_FILESTORE"
            echo "✅ Filestore restaurado"
        fi
        
        rm -rf "$SAFETY_BACKUP_DIR"
    fi
    
    # Reiniciar servicio
    echo "🔧 Reiniciando servicio..."
    sudo systemctl start "$SERVICE_NAME"
    
    cleanup
    echo ""
    echo "✅ Rollback completado. Sistema restaurado al estado anterior."
    exit 1
}

# Trap para manejar errores
trap rollback ERR

# PASO 1: Crear backup de seguridad
echo "💾 PASO 1/6: Creando backup de seguridad..."
mkdir -p "$SAFETY_BACKUP_DIR"

echo "  → Exportando base de datos actual..."
sudo -u postgres pg_dump "$PROD_DB" > "$SAFETY_BACKUP_DIR/dump.sql"
SAFETY_DB_SIZE=$(du -h "$SAFETY_BACKUP_DIR/dump.sql" | cut -f1)
echo "  ✅ Base de datos: $SAFETY_DB_SIZE"

if [ -d "$PROD_FILESTORE" ]; then
    echo "  → Copiando filestore actual..."
    cp -r "$PROD_FILESTORE" "$SAFETY_BACKUP_DIR/filestore"
    SAFETY_FS_SIZE=$(du -sh "$SAFETY_BACKUP_DIR/filestore" | cut -f1)
    echo "  ✅ Filestore: $SAFETY_FS_SIZE"
else
    echo "  ⚠️  No hay filestore actual"
fi

echo "✅ Backup de seguridad creado"
echo ""

# PASO 2: Detener servicio
echo "🛑 PASO 2/6: Deteniendo servicio Odoo..."
sudo systemctl stop "$SERVICE_NAME"
sleep 2
echo "✅ Servicio detenido"
echo ""

# PASO 3: Extraer backup
echo "📦 PASO 3/6: Extrayendo backup..."
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"

# Validar contenido del backup
if [ ! -f "$TEMP_DIR/dump.sql" ]; then
    echo "❌ Error: El backup no contiene dump.sql"
    rollback
fi

if [ ! -d "$TEMP_DIR/filestore" ]; then
    echo "⚠️  Advertencia: El backup no contiene filestore"
    mkdir -p "$TEMP_DIR/filestore"
fi

echo "✅ Backup extraído"
echo ""

# PASO 4: Restaurar base de datos
echo "🗄️  PASO 4/6: Restaurando base de datos..."
echo "  → Eliminando base de datos actual..."
sudo -u postgres dropdb --if-exists "$PROD_DB"

echo "  → Creando nueva base de datos..."
sudo -u postgres createdb -O "$USER" "$PROD_DB"

echo "  → Importando datos..."
sudo -u postgres psql -d "$PROD_DB" < "$TEMP_DIR/dump.sql" > /dev/null 2>&1

RESTORED_DB_SIZE=$(sudo -u postgres psql -d "$PROD_DB" -t -c "SELECT pg_size_pretty(pg_database_size('$PROD_DB'));" | xargs)
echo "✅ Base de datos restaurada: $RESTORED_DB_SIZE"
echo ""

# PASO 5: Restaurar filestore
echo "📁 PASO 5/6: Restaurando filestore..."
echo "  → Eliminando filestore actual..."
rm -rf "$PROD_FILESTORE"

echo "  → Copiando nuevo filestore..."
cp -r "$TEMP_DIR/filestore" "$PROD_FILESTORE"

FILE_COUNT=$(find "$PROD_FILESTORE" -type f | wc -l)
FS_SIZE=$(du -sh "$PROD_FILESTORE" | cut -f1)
echo "✅ Filestore restaurado: $FS_SIZE ($FILE_COUNT archivos)"
echo ""

# PASO 6: Reiniciar servicio
echo "🔧 PASO 6/6: Reiniciando servicio Odoo..."
sudo systemctl start "$SERVICE_NAME"
sleep 3

# Verificar que el servicio está activo
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Servicio iniciado correctamente"
else
    echo "❌ Error: El servicio no pudo iniciarse"
    rollback
fi

# Limpiar
cleanup
rm -rf "$SAFETY_BACKUP_DIR"

echo ""
echo "✅ ============================================"
echo "   RESTAURACIÓN COMPLETADA EXITOSAMENTE"
echo "============================================"
echo ""
echo "📊 Resumen:"
echo "   • Base de datos: $RESTORED_DB_SIZE"
echo "   • Filestore: $FS_SIZE ($FILE_COUNT archivos)"
echo "   • Servicio: Activo"
echo ""
echo "🎉 El sistema de producción ha sido restaurado"
echo ""

# Registrar en log
LOG_FILE="$BACKUP_DIR/restore.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Restore: $BACKUP_FILE - DB: $RESTORED_DB_SIZE - Files: $FILE_COUNT - Status: OK" >> "$LOG_FILE"
