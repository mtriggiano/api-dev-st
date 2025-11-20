#!/bin/bash
# Script para neutralizar base de datos de Odoo usando SQL directo
# No requiere importar el módulo Odoo

set -e

DB_NAME="$1"

if [[ -z "$DB_NAME" ]]; then
    echo "❌ Debes proporcionar el nombre de la base de datos"
    echo "   Uso: $0 <nombre_base_datos>"
    exit 1
fi

echo "🔄 Neutralizando base de datos: $DB_NAME"

# Verificar que la base de datos existe
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "❌ La base de datos $DB_NAME no existe"
    exit 1
fi

echo "🛡️  Aplicando neutralización..."

# Ejecutar neutralización con SQL
sudo -u postgres psql -d "$DB_NAME" << 'EOF'
-- Desactivar todos los crons
UPDATE ir_cron SET active = false WHERE active = true;

-- Desactivar envío de correos
UPDATE ir_mail_server SET active = false WHERE active = true;

-- Limpiar colas de correo pendientes
DELETE FROM mail_mail WHERE state IN ('outgoing', 'exception');

-- Desactivar webhooks
UPDATE webhook_address SET active = false WHERE active = true;

-- Eliminar tokens de acceso
DELETE FROM auth_api_key;

-- Limpiar sesiones activas
DELETE FROM ir_session;

-- Desactivar acciones automáticas (automated actions)
UPDATE base_automation SET active = false WHERE active = true;

-- Eliminar licencia Enterprise (si existe)
DELETE FROM ir_config_parameter WHERE key = 'database.enterprise_code';
DELETE FROM ir_config_parameter WHERE key = 'database.expiration_date';
DELETE FROM ir_config_parameter WHERE key = 'database.expiration_reason';

-- Desactivar modo producción
UPDATE ir_config_parameter SET value = 'False' WHERE key = 'database.is_neutralized';

-- Limpiar tokens de OAuth
DELETE FROM auth_oauth_provider WHERE enabled = true;

-- Desactivar notificaciones push
UPDATE ir_config_parameter SET value = '' WHERE key = 'ocn.ocn_push_notification';

-- Limpiar trabajos en cola
DELETE FROM queue_job WHERE state IN ('pending', 'enqueued', 'started');

-- Mensaje de confirmación
SELECT '✅ Neutralización completada' as status;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Base de datos neutralizada correctamente"
    echo "   - Crons desactivados"
    echo "   - Correos desactivados"
    echo "   - Webhooks desactivados"
    echo "   - Licencia Enterprise eliminada"
    echo "   - Sesiones limpiadas"
else
    echo "❌ Error al neutralizar base de datos"
    exit 1
fi
