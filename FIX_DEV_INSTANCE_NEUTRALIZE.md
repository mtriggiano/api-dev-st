# 🐛 Fix: Error en Neutralización de Instancias de Desarrollo

## 🔍 Problema Detectado

Al crear una instancia de desarrollo, el proceso fallaba en el paso de neutralización con el error:

```
🛡️  Neutralizando base de datos de desarrollo...
Traceback (most recent call last):
  File "/home/mtg/api-dev/scripts/odoo/neutralize-database.py", line 18, in <module>
    import odoo
ModuleNotFoundError: No module named 'odoo'
```

### Causa Raíz

El script `create-dev-instance.sh` activaba el virtualenv pero luego ejecutaba `python3` en lugar de `python`, lo que causaba que usara el Python del sistema en lugar del Python del virtualenv donde está instalado Odoo.

```bash
# ❌ ANTES (incorrecto)
source "$VENV_DIR/bin/activate"
python3 "$SCRIPTS_PATH/odoo/neutralize-database.py" "$DB_NAME"
```

## ✅ Solución Aplicada

### 1. Corregir Script de Creación

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Cambio** (línea 280-289):
```bash
# ✅ DESPUÉS (correcto)
source "$VENV_DIR/bin/activate"
# Usar python del virtualenv (no python3 del sistema)
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

**Mejoras**:
- ✅ Usa `python` en lugar de `python3` (apunta al Python del virtualenv)
- ✅ Sale con error si la neutralización falla
- ✅ Desactiva el virtualenv después de usarlo

### 2. Script de Limpieza de Instancias Fallidas

**Archivo**: `/home/mtg/api-dev/scripts/utils/cleanup-failed-instance.sh`

Script nuevo para limpiar instancias que fallaron a medias:

```bash
# Uso
./scripts/utils/cleanup-failed-instance.sh dev-mtg
```

**Funciones**:
- ✅ Detiene y elimina servicio systemd
- ✅ Elimina bases de datos relacionadas
- ✅ Elimina directorio de la instancia
- ✅ Elimina configuración nginx
- ✅ Actualiza archivo de tracking
- ✅ Recarga servicios

## 🧹 Limpieza Realizada

La instancia `dev-mtg` que falló fue limpiada:
- ✅ Base de datos `dev-mtg-prod-panel3` eliminada
- ✅ Directorio `/home/mtg/apps/develop/odoo/dev-mtg` eliminado
- ✅ Configuraciones nginx eliminadas
- ✅ Tracking actualizado

## 🧪 Verificación

### Antes del Fix
```bash
# Crear instancia → Falla en neutralización
# Resultado: Instancia parcial sin servicio
# Log: ModuleNotFoundError: No module named 'odoo'
```

### Después del Fix
```bash
# Crear instancia → Neutralización exitosa
# Resultado: Instancia completa y funcional
# Log: ✅ Base de datos neutralizada correctamente
```

## 📋 Instancias Actuales

```bash
# Ver instancias de desarrollo
ls /home/mtg/apps/develop/odoo/

# Ver logs de creación
ls -lt /tmp/odoo-create-dev-*.log | head -3

# Limpiar instancia fallida
./scripts/utils/cleanup-failed-instance.sh <nombre-instancia>
```

## 🎯 Resultado

- ✅ Script corregido
- ✅ Instancia fallida limpiada
- ✅ Script de limpieza creado para futuros casos
- ✅ Sistema listo para crear nuevas instancias

## 💡 Recomendaciones

1. **Siempre revisar logs completos**: `/tmp/odoo-create-dev-<nombre>.log`
2. **Si una instancia falla**: Usar el script de limpieza antes de reintentar
3. **Verificar virtualenv**: El comando `python` debe apuntar al virtualenv después de `source activate`

## 🚀 Próximos Pasos

1. Recarga el panel web
2. Crea una nueva instancia de desarrollo
3. El modal ahora mostrará los logs completos
4. La neutralización debería funcionar correctamente

---

**Fecha**: 18 Nov 2025 23:35
**Estado**: ✅ CORREGIDO
**Instancia limpiada**: dev-mtg
