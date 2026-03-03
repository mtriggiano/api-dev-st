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
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB_NAME" << 'EOF'
-- Desactivar todos los crons
UPDATE ir_cron SET active = false WHERE active = true;

-- Desactivar envío de correos
UPDATE ir_mail_server SET active = false WHERE active = true;

-- Limpiar colas de correo pendientes
DELETE FROM mail_mail WHERE state IN ('outgoing', 'exception');

-- Desactivar webhooks (si el módulo existe)
DO $$
BEGIN
    IF to_regclass('public.webhook_address') IS NOT NULL THEN
        EXECUTE 'UPDATE webhook_address SET active = false WHERE active = true';
    END IF;
END
$$;

-- Eliminar tokens de acceso (si el módulo existe)
DO $$
BEGIN
    IF to_regclass('public.auth_api_key') IS NOT NULL THEN
        EXECUTE 'DELETE FROM auth_api_key';
    END IF;
END
$$;

-- Limpiar sesiones activas (si la tabla existe)
DO $$
BEGIN
    IF to_regclass('public.ir_session') IS NOT NULL THEN
        EXECUTE 'DELETE FROM ir_session';
    END IF;
END
$$;

-- Desactivar acciones automáticas (si el módulo existe)
DO $$
BEGIN
    IF to_regclass('public.base_automation') IS NOT NULL THEN
        EXECUTE 'UPDATE base_automation SET active = false WHERE active = true';
    END IF;
END
$$;

-- Eliminar licencia Enterprise (si existe)
DELETE FROM ir_config_parameter WHERE key = 'database.enterprise_code';
DELETE FROM ir_config_parameter WHERE key = 'database.expiration_date';
DELETE FROM ir_config_parameter WHERE key = 'database.expiration_reason';

-- Marcar explícitamente la base como neutralizada
INSERT INTO ir_config_parameter (key, value)
VALUES ('database.is_neutralized', 'True')
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value;

-- Activar indicadores visuales de neutralización (franja/etiqueta)
UPDATE ir_ui_view
   SET active = true
 WHERE key IN ('web.neutralize_banner', 'website.neutralize_ribbon');

-- Limpiar tokens/proveedores OAuth (si el módulo existe)
DO $$
BEGIN
    IF to_regclass('public.auth_oauth_provider') IS NOT NULL THEN
        EXECUTE 'DELETE FROM auth_oauth_provider WHERE enabled = true';
    END IF;
END
$$;

-- Desactivar notificaciones push
INSERT INTO ir_config_parameter (key, value)
VALUES ('ocn.ocn_push_notification', '')
ON CONFLICT (key) DO UPDATE
SET value = EXCLUDED.value;

-- Limpiar trabajos en cola
DO $$
BEGIN
    IF to_regclass('public.queue_job') IS NOT NULL THEN
        EXECUTE 'DELETE FROM queue_job WHERE state IN (''pending'', ''enqueued'', ''started'')';
    END IF;
END
$$;

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
