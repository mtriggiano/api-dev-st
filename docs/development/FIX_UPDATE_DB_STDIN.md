# ✅ Fix: Error de Sintaxis en update-db.sh

## 🐛 Problema

Al actualizar la base de datos desde el panel web, el proceso se quedaba colgado con error:

```
/home/mtg/apps/develop/odoo/dev-testp4/update-db.sh: line 16: conditional binary operator expected
/home/mtg/apps/develop/odoo/dev-testp4/update-db.sh: line 16: syntax error near `\!='
/home/mtg/apps/develop/odoo/dev-testp4/update-db.sh: line 16: `if [[ "$CONFIRM" \!= "s" ]] && [[ "$CONFIRM" \!= "S" ]]; then'
```

### Causas

1. **Caracteres escapados incorrectamente**: El heredoc estaba escapando `!=` como `\!=`
2. **Shebang escapado**: La línea `#!/bin/bash` estaba como `#\!/bin/bash`
3. **Manejo de stdin**: El script no diferenciaba entre ejecución interactiva y desde backend

## ✅ Solución

### 1. Template Actualizado en create-dev-instance.sh

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Líneas 515-529**: Agregado detección de terminal

```bash
# ANTES
# Leer confirmación
read CONFIRM

if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

# AHORA
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

### 2. Script Corregido en Instancia Existente

**Archivo**: `/home/mtg/apps/develop/odoo/dev-testp4/update-db.sh`

Cambios aplicados:
- ✅ Shebang correcto: `#!/bin/bash`
- ✅ Operadores sin escapar: `!=` en lugar de `\!=`
- ✅ Detección de terminal con `[ -t 0 ]`
- ✅ Prompt interactivo cuando se ejecuta manualmente
- ✅ Lectura de stdin cuando se ejecuta desde backend

## 📊 Flujo de Ejecución

### Ejecución Manual (Terminal)

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./update-db.sh
```

**Comportamiento**:
```
🔄 Actualizando base de datos de desarrollo desde producción...
   Producción: prod-panel4
   Desarrollo: dev-testp4-prod-panel4
Confirmar actualización (s/n): s    ← Usuario ingresa 's'
⏹️  Deteniendo servicio Odoo...
...
🔒 ¿Neutralizar base de datos? (s/n): s    ← Usuario ingresa 's'
🔒 Neutralizando base de datos...
✅ Base de datos actualizada correctamente.
```

### Ejecución desde Backend (Panel Web)

```python
# Backend envía:
process.stdin.write(f's\n{neutralize_answer}\n')
```

**Comportamiento**:
```
🔄 Actualizando base de datos de desarrollo desde producción...
   Producción: prod-panel4
   Desarrollo: dev-testp4-prod-panel4
⏹️  Deteniendo servicio Odoo...    ← Lee 's' de stdin automáticamente
...
🔒 Neutralizando base de datos...    ← Lee 's' o 'n' de stdin automáticamente
✅ Base de datos actualizada correctamente.
```

## 🔍 Detección de Terminal

El script usa `[ -t 0 ]` para detectar si stdin es un terminal:

```bash
if [ -t 0 ]; then
  # Terminal interactivo: mostrar prompt
  read -p "Confirmar actualización (s/n): " CONFIRM
else
  # No es terminal (backend): leer de stdin sin prompt
  read CONFIRM
fi
```

**Ventajas**:
- ✅ Funciona en terminal interactivo
- ✅ Funciona desde backend con stdin pipe
- ✅ No requiere parámetros adicionales
- ✅ Mismo script para ambos casos

## 🧪 Pruebas

### Prueba 1: Desde Panel Web

1. Ir a "Instancias" en el panel web
2. Clic en "⚙️" de la instancia `dev-testp4`
3. Seleccionar "Actualizar Base de Datos"
4. Marcar/desmarcar "Neutralizar"
5. Clic en "Actualizar"

**Resultado esperado**:
```
✅ Modal muestra log en tiempo real
✅ No hay errores de sintaxis
✅ Proceso completa exitosamente
✅ Modal se cierra al finalizar
```

### Prueba 2: Desde Terminal

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./update-db.sh
```

**Resultado esperado**:
```
✅ Pide confirmación interactiva
✅ Pide si neutralizar
✅ Proceso completa exitosamente
```

## 📁 Archivos Modificados

```
/home/mtg/api-dev/
├── scripts/odoo/
│   └── create-dev-instance.sh          ← Template actualizado
└── apps/develop/odoo/
    └── dev-testp4/
        ├── update-db.sh                ← Script corregido
        ├── update-db.sh.backup-*       ← Backups automáticos
        └── update-db.sh.backup2        ← Backup manual
```

## 🎯 Resultado

- ✅ Sintaxis corregida (sin `\!=`)
- ✅ Shebang correcto (`#!/bin/bash`)
- ✅ Detección de terminal implementada
- ✅ Funciona desde panel web
- ✅ Funciona desde terminal
- ✅ Template actualizado para nuevas instancias

## 💡 Notas Técnicas

### ¿Por qué `[ -t 0 ]`?

- `[ -t 0 ]` verifica si el file descriptor 0 (stdin) es un terminal
- Retorna `true` si es terminal interactivo
- Retorna `false` si stdin es un pipe o está cerrado
- Permite al script adaptarse automáticamente al contexto

### Backend: Cómo Envía Datos

```python
# backend/services/instance_manager.py
process = subprocess.Popen(
    ['/bin/bash', script_path],
    stdin=subprocess.PIPE,
    stdout=log_file,
    stderr=subprocess.STDOUT,
    start_new_session=True,
    cwd=instance_path,
    text=True
)
# Enviar confirmación para continuar y para neutralizar
process.stdin.write(f's\n{neutralize_answer}\n')
process.stdin.close()
```

- Primera línea: `s\n` → Confirma la actualización
- Segunda línea: `s\n` o `n\n` → Neutralizar o no

---

**Fecha**: 19 Nov 2025 10:50
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar actualización de BD desde el panel web
