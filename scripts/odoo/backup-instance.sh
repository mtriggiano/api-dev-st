#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 💾 Script de backup para una instancia específica de Odoo
# Compatible con formato estándar de Odoo Online
# Estructura: backup.tar.gz contiene dump.sql + filestore/

set -e

# Verificar que se proporcionó el nombre de la instancia
INSTANCE_NAME="$1"

if [ -z "$INSTANCE_NAME" ]; then
  echo "❌ Error: Debe especificar el nombre de la instancia"
  echo "Uso: $0 <instance_name>"
  exit 1
fi

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"

# Configuración
BACKUP_BASE_DIR="${BACKUPS_PATH:-/home/mtg/backups}"
INSTANCE_BACKUP_DIR="$BACKUP_BASE_DIR/instances/$INSTANCE_NAME"
CONFIG_FILE="$INSTANCE_BACKUP_DIR/config.json"
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"

# Crear directorio de la instancia si no existe
mkdir -p "$INSTANCE_BACKUP_DIR"

# Leer configuración de la instancia (si existe)
if [ -f "$CONFIG_FILE" ]; then
  RETENTION_DAYS=$(jq -r '.retention_days // 7' "$CONFIG_FILE" 2>/dev/null || echo "7")
  AUTO_ENABLED=$(jq -r '.auto_backup_enabled // true' "$CONFIG_FILE" 2>/dev/null || echo "true")
else
  RETENTION_DAYS=7
  AUTO_ENABLED=true
fi

# Verificar si el backup automático está habilitado (solo para cron)
if [ "$AUTO_ENABLED" != "true" ] && [ -t 0 ]; then
  # Si se ejecuta desde terminal (manual), permitir
  :
elif [ "$AUTO_ENABLED" != "true" ]; then
  # Si se ejecuta desde cron y está deshabilitado, salir
  echo "⏸️  Backup automático deshabilitado para $INSTANCE_NAME"
  exit 0
fi

# Obtener información de la instancia
DB_NAME="$INSTANCE_NAME"
FILESTORE_PATH="$FILESTORE_BASE/$DB_NAME"

# Timestamp para el backup
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="$INSTANCE_BACKUP_DIR/$BACKUP_NAME"

echo "💾 Iniciando backup de $INSTANCE_NAME..."
echo "   Base de datos: $DB_NAME"
echo "   Timestamp: $TIMESTAMP"
echo ""

# Crear directorio temporal para este backup
mkdir -p "$BACKUP_PATH"

# 1. Backup de la base de datos (dump.sql sin comprimir, como Odoo Online)
echo "🗄️  Creando dump de base de datos..."
if sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_PATH/dump.sql" 2>/dev/null; then
  DB_SIZE=$(du -h "$BACKUP_PATH/dump.sql" | cut -f1)
  echo "✅ Base de datos: $DB_SIZE"
else
  echo "❌ Error al crear dump de base de datos"
  rm -rf "$BACKUP_PATH"
  exit 1
fi

# 2. Copiar filestore (estructura de carpetas, como Odoo Online)
if [ -d "$FILESTORE_PATH" ]; then
  echo "📁 Copiando filestore..."
  cp -r "$FILESTORE_PATH" "$BACKUP_PATH/filestore"
  FILE_COUNT=$(find "$BACKUP_PATH/filestore" -type f 2>/dev/null | wc -l)
  FS_SIZE=$(du -sh "$BACKUP_PATH/filestore" 2>/dev/null | cut -f1)
  echo "✅ Filestore: $FS_SIZE ($FILE_COUNT archivos)"
else
  echo "⚠️  No se encontró filestore en $FILESTORE_PATH"
  mkdir -p "$BACKUP_PATH/filestore"
  FILE_COUNT=0
  FS_SIZE="0"
fi

# 3. Comprimir todo en formato estándar Odoo
echo "📦 Creando archivo tar.gz..."
cd "$INSTANCE_BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" -C "$BACKUP_NAME" .
rm -rf "$BACKUP_PATH"

TOTAL_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
TOTAL_SIZE_BYTES=$(stat -c%s "${BACKUP_NAME}.tar.gz" 2>/dev/null || stat -f%z "${BACKUP_NAME}.tar.gz")
echo "✅ Backup completado: ${BACKUP_NAME}.tar.gz ($TOTAL_SIZE)"

# 4. Limpiar backups antiguos según retención
echo "🧹 Limpiando backups antiguos (retención: $RETENTION_DAYS días)..."
find "$INSTANCE_BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null
REMAINING=$(ls -1 "$INSTANCE_BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)
echo "✅ Backups restantes: $REMAINING"

# 5. Actualizar configuración de la instancia
if command -v jq >/dev/null 2>&1 && [ -f "$CONFIG_FILE" ]; then
  CURRENT_DATE=$(date '+%Y-%m-%d %H:%M:%S')
  TOTAL_SIZE_ALL=$(du -sb "$INSTANCE_BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | awk '{sum+=$1} END {print sum}')
  
  jq --arg date "$CURRENT_DATE" \
     --arg status "success" \
     --arg size "$TOTAL_SIZE_BYTES" \
     --arg count "$REMAINING" \
     --arg total "$TOTAL_SIZE_ALL" \
     '.last_backup = $date | .last_backup_status = $status | .last_backup_size = ($size | tonumber) | .backup_count = ($count | tonumber) | .total_size = ($total | tonumber)' \
     "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
fi

# 6. Registrar en log
LOG_FILE="$INSTANCE_BACKUP_DIR/backup.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup: ${BACKUP_NAME}.tar.gz - Size: $TOTAL_SIZE - Files: $FILE_COUNT - Status: OK" >> "$LOG_FILE"

echo ""
echo "✅ Backup de $INSTANCE_NAME completado exitosamente"
echo "   Archivo: ${BACKUP_NAME}.tar.gz"
echo "   Tamaño: $TOTAL_SIZE"
echo "   Backups totales: $REMAINING"
