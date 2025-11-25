#!/bin/bash

# Script para sincronizar instancias de producción con el sistema de backups V2
# Lee las instancias activas y crea sus directorios de backup si no existen

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_INSTANCES_DIR="/home/mtg/backups/instances"
PROD_INSTANCES_FILE="/home/mtg/api-dev/data/prod-instances.txt"

echo -e "${GREEN}=== Sincronizando instancias de producción con Backups V2 ===${NC}"

# Crear directorio base si no existe
mkdir -p "$BACKUP_INSTANCES_DIR"

# Contador
count=0

# Leer instancias activas
if [ -f "$PROD_INSTANCES_FILE" ]; then
    # Leer línea por línea
    while IFS= read -r line || [ -n "$line" ]; do
        # Saltar líneas vacías
        if [ -z "$line" ]; then
            continue
        fi
        
        # Extraer nombre de instancia (primera parte antes del |)
        instance_name=$(echo "$line" | cut -d'|' -f1)
        
        # Saltar si está vacío
        if [ -z "$instance_name" ]; then
            continue
        fi
        
        # Crear directorio de la instancia si no existe
        instance_dir="$BACKUP_INSTANCES_DIR/$instance_name"
        
        if [ ! -d "$instance_dir" ]; then
            echo -e "${YELLOW}Creando directorio para: $instance_name${NC}"
            mkdir -p "$instance_dir"
            
            # Crear configuración por defecto
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            cat > "$instance_dir/config.json" << EOFCONFIG
{
  "instance_name": "$instance_name",
  "auto_backup_enabled": false,
  "schedule": "0 3 * * *",
  "retention_days": 7,
  "priority": "medium",
  "last_backup": null,
  "last_backup_status": null,
  "last_backup_size": 0,
  "backup_count": 0,
  "total_size": 0,
  "created_at": "$timestamp",
  "updated_at": "$timestamp"
}
EOFCONFIG
            ((count++))
        else
            echo -e "${GREEN}✓ $instance_name ya existe${NC}"
        fi
    done < "$PROD_INSTANCES_FILE"
else
    echo -e "${YELLOW}Advertencia: No se encontró $PROD_INSTANCES_FILE${NC}"
fi

echo ""
echo -e "${GREEN}=== Sincronización completada ===${NC}"
echo -e "${YELLOW}Instancias nuevas creadas: $count${NC}"
echo -e "${YELLOW}Directorio de backups: $BACKUP_INSTANCES_DIR${NC}"
echo ""
echo "Ahora puedes ver todas las instancias en Backups V2"
