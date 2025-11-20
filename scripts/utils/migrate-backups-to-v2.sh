#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 🔄 Script de migración de backups al sistema V2
# Migra backups existentes del sistema antiguo a la nueva estructura multi-instancia

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Migración de Backups al Sistema V2"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-env.sh"

# Configuración
OLD_BACKUP_DIR="${BACKUPS_PATH:-/home/mtg/backups}"
NEW_INSTANCES_DIR="$OLD_BACKUP_DIR/instances"
PROD_INSTANCES_FILE="/home/mtg/api-dev/data/prod-instances.txt"

# Verificar que existe el directorio de backups antiguo
if [ ! -d "$OLD_BACKUP_DIR" ]; then
  echo "❌ No se encontró el directorio de backups: $OLD_BACKUP_DIR"
  exit 1
fi

# Crear directorio de instancias si no existe
mkdir -p "$NEW_INSTANCES_DIR"

echo "📂 Directorio de backups: $OLD_BACKUP_DIR"
echo "📂 Directorio de instancias: $NEW_INSTANCES_DIR"
echo ""

# Buscar backups existentes en el formato antiguo
OLD_BACKUPS=$(find "$OLD_BACKUP_DIR" -maxdepth 1 -name "backup_*.tar.gz" -type f 2>/dev/null || true)

if [ -z "$OLD_BACKUPS" ]; then
  echo "ℹ️  No se encontraron backups en formato antiguo"
  echo ""
else
  echo "📦 Backups encontrados en formato antiguo:"
  echo "$OLD_BACKUPS" | while read -r backup; do
    echo "   - $(basename "$backup")"
  done
  echo ""
  
  # Intentar determinar la instancia de producción
  if [ -f "$PROD_INSTANCES_FILE" ]; then
    PROD_INSTANCE=$(head -1 "$PROD_INSTANCES_FILE" 2>/dev/null || echo "")
  else
    PROD_INSTANCE=""
  fi
  
  if [ -z "$PROD_INSTANCE" ]; then
    echo "⚠️  No se pudo determinar la instancia de producción automáticamente"
    echo "   Por favor, ingresa el nombre de la instancia de producción:"
    read -r PROD_INSTANCE
    
    if [ -z "$PROD_INSTANCE" ]; then
      echo "❌ Nombre de instancia requerido"
      exit 1
    fi
  fi
  
  echo "🎯 Instancia de producción detectada: $PROD_INSTANCE"
  echo ""
  
  # Crear directorio para la instancia
  INSTANCE_DIR="$NEW_INSTANCES_DIR/$PROD_INSTANCE"
  mkdir -p "$INSTANCE_DIR"
  
  echo "📦 Migrando backups a: $INSTANCE_DIR"
  
  # Mover backups
  MOVED_COUNT=0
  echo "$OLD_BACKUPS" | while read -r backup; do
    if [ -f "$backup" ]; then
      BACKUP_NAME=$(basename "$backup")
      mv "$backup" "$INSTANCE_DIR/"
      echo "   ✅ Migrado: $BACKUP_NAME"
      MOVED_COUNT=$((MOVED_COUNT + 1))
    fi
  done
  
  echo ""
  echo "✅ Backups migrados exitosamente"
  echo ""
fi

# Crear configuración para cada instancia de producción
echo "🔧 Creando configuraciones para instancias..."
echo ""

if [ -f "$PROD_INSTANCES_FILE" ]; then
  while IFS= read -r instance_name; do
    [ -z "$instance_name" ] && continue
    
    INSTANCE_DIR="$NEW_INSTANCES_DIR/$instance_name"
    CONFIG_FILE="$INSTANCE_DIR/config.json"
    
    # Crear directorio si no existe
    mkdir -p "$INSTANCE_DIR"
    
    # Si ya existe config, no sobrescribir
    if [ -f "$CONFIG_FILE" ]; then
      echo "   ℹ️  $instance_name: Config ya existe, omitiendo"
      continue
    fi
    
    # Contar backups existentes
    BACKUP_COUNT=$(ls -1 "$INSTANCE_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)
    
    # Calcular tamaño total
    TOTAL_SIZE=0
    if [ $BACKUP_COUNT -gt 0 ]; then
      TOTAL_SIZE=$(du -sb "$INSTANCE_DIR"/backup_*.tar.gz 2>/dev/null | awk '{sum+=$1} END {print sum}')
    fi
    
    # Obtener último backup
    LAST_BACKUP=""
    LAST_BACKUP_SIZE=0
    LAST_BACKUP_FILE=$(ls -1t "$INSTANCE_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LAST_BACKUP_FILE" ]; then
      LAST_BACKUP=$(stat -c%y "$LAST_BACKUP_FILE" 2>/dev/null | cut -d'.' -f1 || date '+%Y-%m-%d %H:%M:%S')
      LAST_BACKUP_SIZE=$(stat -c%s "$LAST_BACKUP_FILE" 2>/dev/null || stat -f%z "$LAST_BACKUP_FILE" 2>/dev/null || echo "0")
    fi
    
    # Crear configuración por defecto
    cat > "$CONFIG_FILE" << EOF
{
  "instance_name": "$instance_name",
  "auto_backup_enabled": false,
  "schedule": "0 3 * * *",
  "retention_days": 7,
  "priority": "medium",
  "last_backup": ${LAST_BACKUP:+\"$LAST_BACKUP\"},
  "last_backup_status": "migrated",
  "last_backup_size": $LAST_BACKUP_SIZE,
  "backup_count": $BACKUP_COUNT,
  "total_size": $TOTAL_SIZE,
  "created_at": "$(date '+%Y-%m-%d %H:%M:%S')",
  "updated_at": "$(date '+%Y-%m-%d %H:%M:%S')"
}
EOF
    
    echo "   ✅ $instance_name: Config creada ($BACKUP_COUNT backups, $(numfmt --to=iec $TOTAL_SIZE 2>/dev/null || echo "${TOTAL_SIZE} bytes"))"
    
  done < "$PROD_INSTANCES_FILE"
else
  echo "   ⚠️  No se encontró archivo de instancias: $PROD_INSTANCES_FILE"
  echo "   Las configuraciones se crearán automáticamente al usar el sistema"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Migración completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Resumen:"
echo "   • Backups migrados a estructura por instancia"
echo "   • Configuraciones creadas para cada instancia"
echo "   • Backups automáticos DESHABILITADOS por defecto"
echo ""
echo "🎯 Próximos pasos:"
echo "   1. Revisa las configuraciones en: $NEW_INSTANCES_DIR"
echo "   2. Activa los backups automáticos desde el panel web"
echo "   3. Configura horarios y retención según necesites"
echo ""
echo "💡 Accede al panel de backups en:"
echo "   https://api-dev.softrigx.com/backups-v2"
echo ""
