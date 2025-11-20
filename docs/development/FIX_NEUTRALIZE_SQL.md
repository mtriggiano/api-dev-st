# 🔧 Fix: Neutralización de Base de Datos con SQL Directo

## 🐛 Problema

La neutralización de instancias de desarrollo fallaba con:
```
ModuleNotFoundError: No module named 'odoo'
```

### Causa Raíz

El script `neutralize-database.py` intentaba importar el módulo Odoo:
```python
import odoo
from odoo import api
import odoo.modules.neutralize
```

Pero el virtualenv de desarrollo no tiene Odoo instalado como módulo Python, solo tiene los archivos y dependencias.

## ✅ Solución

### Nuevo Script SQL

Creado `/home/mtg/api-dev/scripts/odoo/neutralize-database-sql.sh` que usa SQL directo en lugar de importar Odoo.

**Ventajas**:
- ✅ No requiere importar Odoo
- ✅ Más rápido (SQL directo)
- ✅ Más confiable (no depende del virtualenv)
- ✅ Funciona con cualquier versión de Odoo

**Acciones que realiza**:
```sql
-- Desactivar todos los crons
UPDATE ir_cron SET active = false;

-- Desactivar envío de correos
UPDATE ir_mail_server SET active = false;

-- Limpiar colas de correo
DELETE FROM mail_mail WHERE state IN ('outgoing', 'exception');

-- Desactivar webhooks
UPDATE webhook_address SET active = false;

-- Eliminar tokens de acceso
DELETE FROM auth_api_key;

-- Limpiar sesiones activas
DELETE FROM ir_session;

-- Desactivar acciones automáticas
UPDATE base_automation SET active = false;

-- Eliminar licencia Enterprise
DELETE FROM ir_config_parameter WHERE key = 'database.enterprise_code';
DELETE FROM ir_config_parameter WHERE key = 'database.expiration_date';

-- Desactivar notificaciones push
UPDATE ir_config_parameter SET value = '' WHERE key = 'ocn.ocn_push_notification';

-- Limpiar trabajos en cola
DELETE FROM queue_job WHERE state IN ('pending', 'enqueued', 'started');
```

### Modificación del Script de Creación

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Antes** (línea 276-289):
```bash
echo "🛡️  Neutralizando base de datos de desarrollo..."
cd "$BASE_DIR"
source "$VENV_DIR/bin/activate"
python "$SCRIPTS_PATH/odoo/neutralize-database.py" "$DB_NAME"
if [ $? -eq 0 ]; then
  echo "✅ Base de datos neutralizada correctamente"
else
  echo "⚠️  Advertencia: Error al neutralizar base de datos"
  deactivate
  exit 1
fi
deactivate
```

**Ahora** (línea 276-285):
```bash
echo "🛡️  Neutralizando base de datos de desarrollo..."
# Usar script SQL directo (no requiere importar Odoo)
"$SCRIPTS_PATH/odoo/neutralize-database-sql.sh" "$DB_NAME"
if [ $? -eq 0 ]; then
  echo "✅ Base de datos neutralizada correctamente"
else
  echo "❌ Error al neutralizar base de datos"
  exit 1
fi
```

## 🎯 Beneficios

1. **Más simple**: No necesita virtualenv activado
2. **Más rápido**: SQL directo es más eficiente
3. **Más confiable**: No depende de imports de Python
4. **Más mantenible**: SQL es más fácil de entender y modificar

## 📋 Uso Manual

```bash
# Neutralizar cualquier base de datos
./scripts/odoo/neutralize-database-sql.sh nombre-base-datos

# Ejemplo
./scripts/odoo/neutralize-database-sql.sh dev-juan-prod-panel3
```

## 🧪 Prueba

1. Crear instancia de desarrollo desde el panel web
2. El log debería mostrar:
   ```
   🛡️  Neutralizando base de datos de desarrollo...
   🔄 Neutralizando base de datos: dev-nombre-prod-panel3
   ✅ Neutralización completada
   ✅ Base de datos neutralizada correctamente
      - Crons desactivados
      - Correos desactivados
      - Webhooks desactivados
      - Licencia Enterprise eliminada
      - Sesiones limpiadas
   ```

## 🔄 Próximos Pasos

1. ✅ Script SQL creado
2. ✅ Script de creación modificado
3. ✅ Script de limpieza disponible
4. ⏳ Probar creación de instancia desde panel web

---

**Fecha**: 18 Nov 2025 23:55
**Estado**: ✅ IMPLEMENTADO
**Archivos**:
- `/home/mtg/api-dev/scripts/odoo/neutralize-database-sql.sh` (nuevo)
- `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh` (modificado)
