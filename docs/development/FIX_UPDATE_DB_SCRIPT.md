# ✅ Fix: Script update-db.sh en Instancias Existentes

## 🐛 Problema

Al actualizar la base de datos de una instancia de desarrollo usando el script `update-db.sh`, se mostraba:

```
🔒 ¿Neutralizar base de datos? (s/n):
🔒 Neutralizando base de datos...
⚠️  Script de neutralización no encontrado
```

### Causa

El script `update-db.sh` generado dentro de cada instancia tenía código antiguo que buscaba:
- Ruta antigua: `/home/go/api-dev/scripts/odoo/neutralize-database.py`
- Script Python que ya no se usa

## ✅ Solución

### 1. Actualizar Template en create-dev-instance.sh

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Líneas 553-561**: Actualizado el heredoc que genera `update-db.sh`

```bash
# ANTES
NEUTRALIZE_SCRIPT="/home/go/api-dev/scripts/odoo/neutralize-database.py"
if [[ -f "$NEUTRALIZE_SCRIPT" ]]; then
  cd "__BASE_DIR__"
  source venv/bin/activate
  python3 "$NEUTRALIZE_SCRIPT" "$DEV_DB"
  echo "✅ Base de datos neutralizada"
else
  echo "⚠️  Script de neutralización no encontrado"
fi

# AHORA
NEUTRALIZE_SCRIPT="/home/mtg/api-dev/scripts/odoo/neutralize-database-sql.sh"
if [[ -f "$NEUTRALIZE_SCRIPT" ]]; then
  "$NEUTRALIZE_SCRIPT" "$DEV_DB"
else
  echo "⚠️  Script de neutralización no encontrado en: $NEUTRALIZE_SCRIPT"
fi
```

### 2. Script para Actualizar Instancias Existentes

**Archivo**: `/home/mtg/api-dev/scripts/utils/update-existing-scripts.sh`

Script que actualiza automáticamente todos los `update-db.sh` en instancias existentes:

```bash
#!/bin/bash
# Busca todas las instancias en /home/mtg/apps/develop/odoo/
# Para cada una:
#   1. Hace backup del update-db.sh
#   2. Reemplaza la ruta del script de neutralización
#   3. Actualiza el código de ejecución
```

**Uso**:
```bash
./scripts/utils/update-existing-scripts.sh
```

**Resultado**:
```
🔄 Actualizando scripts update-db.sh en instancias existentes...

📝 Actualizando: dev-testp4
   ✅ Actualizado

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Actualización completada
   Actualizados: 1
   Omitidos: 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Los scripts ahora usan: neutralize-database-sql.sh
```

## 📋 Cambios en el Script update-db.sh

### Antes (Incorrecto)
```bash
NEUTRALIZE_SCRIPT="/home/go/api-dev/scripts/odoo/neutralize-database.py"
if [[ -f "$NEUTRALIZE_SCRIPT" ]]; then
  cd "__BASE_DIR__"
  source venv/bin/activate
  python3 "$NEUTRALIZE_SCRIPT" "$DEV_DB"
  echo "✅ Base de datos neutralizada"
else
  echo "⚠️  Script de neutralización no encontrado"
fi
```

### Ahora (Correcto)
```bash
NEUTRALIZE_SCRIPT="/home/mtg/api-dev/scripts/odoo/neutralize-database-sql.sh"
if [[ -f "$NEUTRALIZE_SCRIPT" ]]; then
  "$NEUTRALIZE_SCRIPT" "$DEV_DB"
else
  echo "⚠️  Script de neutralización no encontrado en: $NEUTRALIZE_SCRIPT"
fi
```

## 🎯 Beneficios

1. **Más simple**: No requiere activar virtualenv
2. **Más rápido**: SQL directo es más eficiente
3. **Más confiable**: No depende de imports de Python
4. **Ruta correcta**: Usa `/home/mtg` en lugar de `/home/go`

## 🧪 Prueba

### Actualizar BD de una Instancia

```bash
# Ir al directorio de la instancia
cd /home/mtg/apps/develop/odoo/dev-testp4

# Ejecutar script de actualización
./update-db.sh
```

**Flujo esperado**:
```
🔄 Actualizando base de datos de desarrollo desde producción...
   Producción: prod-panel4
   Desarrollo: dev-testp4-prod-panel4
s
⏹️  Deteniendo servicio Odoo...
🗄️  Eliminando BD de desarrollo actual...
📦 Creando dump de producción...
🔄 Restaurando en desarrollo...
📁 Sincronizando filestore...
✅ Filestore sincronizado (X archivos)

🔒 ¿Neutralizar base de datos? (s/n):
s
🔒 Neutralizando base de datos...
🔄 Neutralizando base de datos: dev-testp4-prod-panel4
✅ Neutralización completada
✅ Base de datos neutralizada correctamente
   - Crons desactivados
   - Correos desactivados
   - Webhooks desactivados
   - Licencia Enterprise eliminada
   - Sesiones limpiadas
🎨 Regenerando assets...
▶️  Iniciando servicio Odoo...
✅ Base de datos actualizada correctamente.
```

## 📁 Archivos Modificados

```
/home/mtg/api-dev/
├── scripts/
│   ├── odoo/
│   │   └── create-dev-instance.sh      ← Template actualizado
│   └── utils/
│       └── update-existing-scripts.sh  ← Nuevo script de actualización
└── apps/develop/odoo/
    └── dev-testp4/
        └── update-db.sh                ← Script actualizado
```

## 🔄 Instancias Futuras

Todas las instancias de desarrollo creadas a partir de ahora tendrán el script `update-db.sh` correcto automáticamente, ya que el template en `create-dev-instance.sh` fue actualizado.

## 📝 Backups

El script de actualización crea backups automáticamente:
```
/home/mtg/apps/develop/odoo/dev-testp4/
├── update-db.sh
├── update-db.sh.backup-20251119-093000
└── update-db.sh.backup2
```

---

**Fecha**: 19 Nov 2025 09:35
**Estado**: ✅ CORREGIDO
**Instancias actualizadas**: 1 (dev-testp4)
