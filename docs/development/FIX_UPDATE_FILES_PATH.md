# ✅ Fix: PATH y stdin en update-files.sh

## 🐛 Problema

Al actualizar archivos desde el panel web, el script fallaba con:

```
▶️  Iniciando servicio Odoo...
/home/mtg/apps/develop/odoo/dev-testp4/update-files.sh: line 49: sudo: command not found
✅ Archivos actualizados correctamente.
```

### Causas

1. **PATH no configurado**: Faltaba `export PATH` al inicio del script
2. **Sin detección de terminal**: No manejaba stdin correctamente cuando se ejecuta desde backend

## ✅ Solución

### 1. Script Existente Corregido

**Archivo**: `/home/mtg/apps/develop/odoo/dev-testp4/update-files.sh`

**Cambios aplicados**:

```bash
# ANTES
#!/bin/bash
# Script para actualizar archivos de desarrollo desde producción

PROD_DIR="/home/mtg/apps/production/odoo/prod-panel4"
...
# Leer confirmación
read CONFIRM

if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

# AHORA
#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para actualizar archivos de desarrollo desde producción

PROD_DIR="/home/mtg/apps/production/odoo/prod-panel4"
...
# Leer confirmación (solo si stdin está disponible)
if [ -t 0 ]; then
  read -p "Confirmar actualización (s/n): " CONFIRM
  if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
    echo "❌ Cancelado."
    exit 1
  fi
else
  # Ejecutado desde backend, leer de stdin
  read CONFIRM
  if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
    echo "❌ Cancelado."
    exit 1
  fi
fi
```

### 2. Template Actualizado

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Líneas 589-616**: Template corregido

```bash
cat > "$BASE_DIR/update-files.sh" <<'UPDATEFILES'
#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para actualizar archivos de desarrollo desde producción
...
# Leer confirmación (solo si stdin está disponible)
if [ -t 0 ]; then
  read -p "Confirmar actualización (s/n): " CONFIRM
  ...
else
  # Ejecutado desde backend, leer de stdin
  read CONFIRM
  ...
fi
```

## 📊 Flujo de Actualización de Archivos

### Desde Panel Web

```
Usuario clic en "Actualizar Archivos"
         ↓
Backend envía: s\n (confirmar)
         ↓
Script detecta: stdin no es terminal
         ↓
Lee 's' de stdin automáticamente
         ↓
⏹️  Detiene servicio
💾 Backup de custom_addons
🗑️  Elimina odoo-server
📦 Copia desde producción
🔄 Restaura custom_addons
🐍 Actualiza dependencias
▶️  Inicia servicio (con PATH correcto)
         ↓
✅ Archivos actualizados correctamente
```

### Desde Terminal

```
cd /home/mtg/apps/develop/odoo/dev-testp4
./update-files.sh
         ↓
Script detecta: stdin es terminal
         ↓
Confirmar actualización (s/n): s    ← Usuario ingresa
         ↓
⏹️  Detiene servicio
...
▶️  Inicia servicio
         ↓
✅ Archivos actualizados correctamente
```

## 🎯 Cambios Aplicados

### Scripts Auxiliares Afectados

1. ✅ **update-db.sh** - Ya corregido anteriormente
2. ✅ **update-files.sh** - Corregido ahora
3. ⚠️  **sync-filestore.sh** - Revisar si necesita corrección
4. ⚠️  **regenerate-assets.sh** - Revisar si necesita corrección

## 🧪 Prueba

### Desde Panel Web

1. Ir a "Instancias"
2. Clic en ⚙️ de `dev-testp4`
3. Seleccionar "Actualizar Archivos"
4. Clic en "Actualizar"

**Resultado esperado**:
```
✅ Log se muestra en tiempo real
✅ No hay error "sudo: command not found"
✅ Servicio se reinicia correctamente
✅ Archivos actualizados desde producción
```

### Desde Terminal

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./update-files.sh
```

**Resultado esperado**:
```
✅ Pide confirmación interactiva
✅ Actualiza archivos correctamente
✅ No hay errores de PATH
```

## 📁 Archivos Modificados

```
/home/mtg/api-dev/
├── scripts/odoo/
│   └── create-dev-instance.sh          ← Template actualizado
└── apps/develop/odoo/
    └── dev-testp4/
        └── update-files.sh             ← Script corregido
```

## 💡 Otros Scripts a Revisar

Los siguientes scripts también se generan y pueden necesitar corrección:

### sync-filestore.sh
```bash
# Verificar si tiene export PATH
# Verificar si maneja stdin correctamente
```

### regenerate-assets.sh
```bash
# Verificar si tiene export PATH
# Verificar si usa sudo
```

## 🔄 Próximos Pasos

1. ✅ update-db.sh corregido
2. ✅ update-files.sh corregido
3. ⏳ Revisar sync-filestore.sh
4. ⏳ Revisar regenerate-assets.sh
5. ⏳ Crear script para actualizar todos los scripts en instancias existentes

---

**Fecha**: 19 Nov 2025 12:30
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar actualización de archivos desde el panel web
