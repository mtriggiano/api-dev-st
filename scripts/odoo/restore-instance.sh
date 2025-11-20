#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 🔄 Script de restauración para una instancia específica de Odoo
# Compatible con formato estándar de Odoo Online

set -e

# Verificar argumentos
INSTANCE_NAME="$1"
BACKUP_FILE="$2"

if [ -z "$INSTANCE_NAME" ] || [ -z "$BACKUP_FILE" ]; then
  echo "❌ Error: Debe especificar el nombre de la instancia y el archivo de backup"
  echo "Uso: $0 <instance_name> <backup_file_path>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "❌ Error: El archivo de backup no existe: $BACKUP_FILE"
  exit 1
fi

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"

# Configuración
DB_NAME="$INSTANCE_NAME"
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
FILESTORE_PATH="$FILESTORE_BASE/$DB_NAME"
TEMP_RESTORE_DIR="/tmp/odoo-restore-$INSTANCE_NAME-$$"
SERVICE_NAME="odoo19e-$INSTANCE_NAME"

echo "🔄 Iniciando restauración de $INSTANCE_NAME..."
echo "   Archivo: $(basename $BACKUP_FILE)"
echo "   Base de datos: $DB_NAME"
echo ""

# Crear directorio temporal
mkdir -p "$TEMP_RESTORE_DIR"

# 1. Extraer backup
echo "📦 Extrayendo backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_RESTORE_DIR"
echo "✅ Backup extraído"

# Verificar estructura
if [ ! -f "$TEMP_RESTORE_DIR/dump.sql" ]; then
  echo "❌ Error: El backup no contiene dump.sql"
  rm -rf "$TEMP_RESTORE_DIR"
  exit 1
fi

# 2. Detener servicio de Odoo
echo "⏹️  Deteniendo servicio Odoo..."
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  sudo systemctl stop "$SERVICE_NAME"
  echo "✅ Servicio detenido"
else
  echo "ℹ️  Servicio no estaba corriendo"
fi

# Esperar a que se libere el puerto
sleep 3

# 3. Restaurar base de datos
echo "🗄️  Restaurando base de datos..."

# Terminar conexiones activas
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';" >/dev/null 2>&1 || true

# Eliminar base de datos existente
echo "   Eliminando base de datos actual..."
sudo -u postgres dropdb "$DB_NAME" 2>/dev/null || true

# Crear nueva base de datos
echo "   Creando base de datos..."
sudo -u postgres createdb "$DB_NAME" -O "mtg" --encoding='UTF8'

# Restaurar dump
echo "   Restaurando datos..."
sudo -u postgres psql -d "$DB_NAME" < "$TEMP_RESTORE_DIR/dump.sql" >/dev/null 2>&1

# Asegurar permisos
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO mtg;" >/dev/null 2>&1
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;" >/dev/null 2>&1
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;" >/dev/null 2>&1

DB_SIZE=$(sudo -u postgres psql -d "$DB_NAME" -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" -t | xargs)
echo "✅ Base de datos restaurada: $DB_SIZE"

# 4. Restaurar filestore
if [ -d "$TEMP_RESTORE_DIR/filestore" ]; then
  echo "📁 Restaurando filestore..."
  
  # Backup del filestore actual (por seguridad)
  if [ -d "$FILESTORE_PATH" ]; then
    BACKUP_FS="$FILESTORE_PATH.backup-$(date +%Y%m%d_%H%M%S)"
    mv "$FILESTORE_PATH" "$BACKUP_FS"
    echo "   Filestore actual respaldado en: $BACKUP_FS"
  fi
  
  # Restaurar nuevo filestore
  mkdir -p "$FILESTORE_BASE"
  cp -r "$TEMP_RESTORE_DIR/filestore" "$FILESTORE_PATH"
  
  # Ajustar permisos
  chown -R mtg:mtg "$FILESTORE_PATH" 2>/dev/null || true
  
  FILE_COUNT=$(find "$FILESTORE_PATH" -type f 2>/dev/null | wc -l)
  FS_SIZE=$(du -sh "$FILESTORE_PATH" 2>/dev/null | cut -f1)
  echo "✅ Filestore restaurado: $FS_SIZE ($FILE_COUNT archivos)"
else
  echo "⚠️  El backup no contiene filestore"
fi

# 5. Limpiar archivos temporales
echo "🧹 Limpiando archivos temporales..."
rm -rf "$TEMP_RESTORE_DIR"
echo "✅ Limpieza completada"

# 6. Iniciar servicio de Odoo
echo "▶️  Iniciando servicio Odoo..."
sudo systemctl start "$SERVICE_NAME"

# Esperar a que inicie
sleep 3

# Verificar estado
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "✅ Servicio iniciado correctamente"
else
  echo "⚠️  El servicio no se inició correctamente"
  echo "   Verifica los logs: sudo journalctl -u $SERVICE_NAME -n 50"
fi

echo ""
echo "✅ Restauración de $INSTANCE_NAME completada exitosamente"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Recomendaciones post-restauración:"
echo "   1. Verifica que la instancia funcione correctamente"
echo "   2. Revisa los logs si hay algún problema:"
echo "      sudo journalctl -u $SERVICE_NAME -n 50"
echo "   3. Prueba el acceso desde el navegador"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
