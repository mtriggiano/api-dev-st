#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 💾 Script de backup completo de producción Odoo
# Compatible con formato estándar de Odoo Online
# Estructura: backup.tar.gz contiene dump.sql + filestore/

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
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
USER="${SYSTEM_USER:-go}"

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Timestamp para el backup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="backup_${PROD_DB}_${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "💾 Iniciando backup de producción (formato Odoo Online)..."
echo "   Instancia: $PROD_INSTANCE"
echo "   Base de datos: $PROD_DB"
echo "   Timestamp: $TIMESTAMP"
echo ""

# Crear directorio temporal para este backup
mkdir -p "$BACKUP_PATH"

# 1. Backup de la base de datos (dump.sql sin comprimir, como Odoo Online)
echo "🗄️  Creando dump de base de datos..."
sudo -u postgres pg_dump "$PROD_DB" > "$BACKUP_PATH/dump.sql"
DB_SIZE=$(du -h "$BACKUP_PATH/dump.sql" | cut -f1)
echo "✅ Base de datos: $DB_SIZE"

# 2. Copiar filestore (estructura de carpetas, como Odoo Online)
if [[ -d "$PROD_FILESTORE" ]]; then
  echo "📁 Copiando filestore..."
  cp -r "$PROD_FILESTORE" "$BACKUP_PATH/filestore"
  FILE_COUNT=$(find "$BACKUP_PATH/filestore" -type f | wc -l)
  FS_SIZE=$(du -sh "$BACKUP_PATH/filestore" | cut -f1)
  echo "✅ Filestore: $FS_SIZE ($FILE_COUNT archivos)"
else
  echo "⚠️  No se encontró filestore en $PROD_FILESTORE"
  mkdir -p "$BACKUP_PATH/filestore"
  FILE_COUNT=0
  FS_SIZE="0"
fi

# 3. Comprimir todo en formato estándar Odoo
echo "📦 Creando archivo tar.gz..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" -C "$BACKUP_NAME" .
rm -rf "$BACKUP_PATH"

TOTAL_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
echo "✅ Backup completado: ${BACKUP_NAME}.tar.gz ($TOTAL_SIZE)"

# 5. Limpiar backups antiguos según retención
echo "🧹 Limpiando backups antiguos (retención: $RETENTION_DAYS días)..."
find "$BACKUP_DIR" -name "backup_${PROD_DB}_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/backup_${PROD_DB}_*.tar.gz 2>/dev/null | wc -l)
echo "✅ Backups restantes: $REMAINING"

# 6. Registrar en log
LOG_FILE="$BACKUP_DIR/backup.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup: ${BACKUP_NAME}.tar.gz - Size: $TOTAL_SIZE - Status: OK" >> "$LOG_FILE"

echo ""
echo "✅ Backup completado exitosamente"
echo "   Archivo: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "   Tamaño: $TOTAL_SIZE"
