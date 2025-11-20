#!/bin/bash
# Script para actualizar los scripts update-db.sh en instancias existentes

DEV_ROOT="/home/mtg/apps/develop/odoo"

echo "🔄 Actualizando scripts update-db.sh en instancias existentes..."
echo ""

if [[ ! -d "$DEV_ROOT" ]]; then
    echo "❌ No se encontró el directorio de instancias de desarrollo"
    exit 1
fi

updated=0
skipped=0

for instance_dir in "$DEV_ROOT"/*; do
    if [[ -d "$instance_dir" ]]; then
        instance_name=$(basename "$instance_dir")
        update_script="$instance_dir/update-db.sh"
        
        if [[ -f "$update_script" ]]; then
            echo "📝 Actualizando: $instance_name"
            
            # Hacer backup
            cp "$update_script" "${update_script}.backup-$(date +%Y%m%d-%H%M%S)"
            
            # Reemplazar con sed simple
            sed -i 's|/home/go/api-dev/scripts/odoo/neutralize-database.py|/home/mtg/api-dev/scripts/odoo/neutralize-database-sql.sh|g' "$update_script"
            
            # Reemplazar el bloque de código Python con el nuevo
            sed -i '/cd "__BASE_DIR__"/,/echo "✅ Base de datos neutralizada"/ {
                /cd "__BASE_DIR__"/d
                /source venv\/bin\/activate/d
                /python3 "$NEUTRALIZE_SCRIPT" "$DEV_DB"/c\    "$NEUTRALIZE_SCRIPT" "$DEV_DB"
            }' "$update_script"
            
            # Actualizar mensaje de error
            sed -i 's|echo "⚠️  Script de neutralización no encontrado"|echo "⚠️  Script de neutralización no encontrado en: $NEUTRALIZE_SCRIPT"|g' "$update_script"
            
            echo "   ✅ Actualizado"
            ((updated++))
        else
            echo "   ⚠️  No tiene update-db.sh: $instance_name"
            ((skipped++))
        fi
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Actualización completada"
echo "   Actualizados: $updated"
echo "   Omitidos: $skipped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Los scripts ahora usan: neutralize-database-sql.sh"
