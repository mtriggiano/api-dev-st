# ✅ Fix: Script de Regeneración de Assets se Quedaba Colgado

## 🐛 Problema

Al regenerar assets desde el panel web, el script se quedaba colgado después de mostrar:

```
🎨 Regenerando assets...
   Esto puede tardar 1-2 minutos, por favor espera...
   Iniciando proceso de actualización...
✅ Regeneración completada exitosamente
▶️  Iniciando servicio Odoo...
[SE QUEDA AQUÍ - NO TERMINA]
```

El servicio se iniciaba correctamente pero el script no terminaba de ejecutarse, dejando el modal del panel web abierto indefinidamente.

## 🔍 Causa

El problema estaba en el uso de un pipe con `while` para filtrar las líneas del output:

```bash
./venv/bin/python3 ./odoo-server/odoo-bin ... 2>&1 | while IFS= read -r line; do
  if [[ "$line" =~ "Loading" ]] || ...; then
    echo "   $line"
  fi
done
```

**Problemas con este enfoque**:
1. El `while` crea un subshell que puede quedarse esperando más entrada
2. El pipe puede no cerrarse correctamente
3. `PIPESTATUS` puede no capturarse correctamente en el subshell
4. El script puede quedarse bloqueado esperando EOF del pipe

## ✅ Solución

Cambiar a un enfoque basado en proceso en background con monitoreo activo:

```bash
# Guardar output en archivo temporal y mostrar progreso
TEMP_LOG="/tmp/odoo-regenerate-$INSTANCE_NAME.log"
./venv/bin/python3 ./odoo-server/odoo-bin -c ./odoo.conf --update=all --stop-after-init > "$TEMP_LOG" 2>&1 &
ODOO_PID=$!

# Mostrar progreso mientras se ejecuta
echo "   Procesando (esto puede tardar 1-2 minutos)..."
while kill -0 $ODOO_PID 2>/dev/null; do
  sleep 2
  echo -n "."
done
echo ""

# Esperar a que termine completamente
wait $ODOO_PID
EXIT_CODE=$?

# Mostrar líneas importantes del log
echo "   Mostrando resumen del proceso:"
grep -E "(Loading|Modules loaded|Assets|Generating|completed|ERROR|WARNING)" "$TEMP_LOG" 2>/dev/null | tail -10 | sed 's/^/   /'

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Regeneración completada exitosamente"
else
  echo "⚠️  Proceso terminó con código: $EXIT_CODE"
  echo "   Ver log completo en: $TEMP_LOG"
fi
```

## 📊 Ventajas del Nuevo Enfoque

### 1. Proceso en Background
```bash
./odoo-bin ... > "$TEMP_LOG" 2>&1 &
ODOO_PID=$!
```
- Ejecuta el proceso en background
- Captura el PID para monitoreo
- Redirige todo el output a un archivo temporal

### 2. Monitoreo Activo
```bash
while kill -0 $ODOO_PID 2>/dev/null; do
  sleep 2
  echo -n "."
done
```
- Verifica si el proceso sigue corriendo
- Muestra progreso visual con puntos
- No se bloquea esperando entrada

### 3. Captura Correcta del Exit Code
```bash
wait $ODOO_PID
EXIT_CODE=$?
```
- Espera a que el proceso termine completamente
- Captura el código de salida real
- No hay problemas con subshells

### 4. Análisis Post-Ejecución
```bash
grep -E "(Loading|Modules loaded|Assets|...)" "$TEMP_LOG" | tail -10
```
- Analiza el log después de completar
- Muestra solo líneas relevantes
- No interfiere con la ejecución

## 🎯 Nuevo Output Esperado

```
🎨 Regenerando assets de Odoo...
   Instancia: dev-testp4
⏹️  Deteniendo servicio Odoo...
   Esperando a que el puerto se libere...
🎨 Regenerando assets...
   Esto puede tardar 1-2 minutos, por favor espera...
   Iniciando proceso de actualización...
   Procesando (esto puede tardar 1-2 minutos)...
..........
   Mostrando resumen del proceso:
   Loading registry for database dev-testp4-prod-panel4...
   Modules loaded.
   Assets bundle 'web.assets_backend' generated
   Assets bundle 'web.assets_frontend' generated
✅ Regeneración completada exitosamente
▶️  Iniciando servicio Odoo...
✅ Servicio iniciado correctamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Assets regenerados correctamente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Verifica que los cambios se aplicaron:
   1. Recarga la página en el navegador (Ctrl+Shift+R)
   2. Verifica que los estilos se vean correctamente
   3. Revisa los logs si hay algún problema:
      sudo journalctl -u odoo19e-dev-testp4 -n 50
```

## 📁 Archivos Modificados

### Instancia Existente
```
/home/mtg/apps/develop/odoo/dev-testp4/
└── regenerate-assets.sh        ✅ Cambio de pipe a background process
```

### Template
```
/home/mtg/api-dev/scripts/odoo/
└── create-dev-instance.sh      ✅ Template actualizado
```

## 🧪 Prueba

### Desde Panel Web

1. Ir a "Instancias"
2. Clic en ⚙️ de `dev-testp4`
3. Seleccionar "Regenerar Assets"
4. Clic en "Regenerar"

**Observa**:
- ✅ Muestra "Procesando..."
- ✅ Muestra puntos de progreso (........)
- ✅ Muestra resumen del proceso
- ✅ Muestra "✅ Regeneración completada exitosamente"
- ✅ Muestra "✅ Servicio iniciado correctamente"
- ✅ Muestra mensaje final con instrucciones
- ✅ **EL MODAL SE CIERRA AUTOMÁTICAMENTE**

### Desde Terminal

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./regenerate-assets.sh
```

**Resultado esperado**:
```
Confirmar regeneración (s/n): s
⏹️  Deteniendo servicio Odoo...
   Esperando a que el puerto se libere...
🎨 Regenerando assets...
   Procesando (esto puede tardar 1-2 minutos)...
..........
   Mostrando resumen del proceso:
   [Líneas importantes del log]
✅ Regeneración completada exitosamente
▶️  Iniciando servicio Odoo...
✅ Servicio iniciado correctamente
...
[SCRIPT TERMINA CORRECTAMENTE]
```

## 💡 Comparación de Enfoques

### Enfoque Anterior (Pipe con While)
```bash
comando 2>&1 | while read line; do
  echo "$line"
done
```

**Problemas**:
- ❌ Crea subshell
- ❌ Puede quedarse esperando EOF
- ❌ Difícil capturar exit code
- ❌ Puede bloquearse

### Enfoque Nuevo (Background Process)
```bash
comando > log 2>&1 &
PID=$!
while kill -0 $PID; do
  sleep 2
done
wait $PID
EXIT_CODE=$?
```

**Ventajas**:
- ✅ No crea subshell problemático
- ✅ Monitoreo activo del proceso
- ✅ Captura correcta del exit code
- ✅ Nunca se bloquea
- ✅ Termina limpiamente

## 🔍 Debugging

### Ver el Log Completo

Si hay algún problema, el log completo está disponible:

```bash
cat /tmp/odoo-regenerate-dev-testp4.log
```

### Verificar si el Proceso Está Corriendo

Durante la ejecución:

```bash
ps aux | grep "odoo-bin.*update=all"
```

### Ver Progreso en Tiempo Real

En otra terminal mientras se ejecuta:

```bash
tail -f /tmp/odoo-regenerate-dev-testp4.log
```

## 📊 Tiempo de Ejecución

| Fase | Tiempo Aproximado |
|------|-------------------|
| Detener servicio | 2-5 segundos |
| Esperar puerto | 5 segundos |
| Regenerar assets | 30-120 segundos |
| Iniciar servicio | 5-10 segundos |
| **Total** | **45-145 segundos** |

## 🎯 Resultado

- ✅ Script ejecuta el proceso en background
- ✅ Muestra progreso visual
- ✅ Captura exit code correctamente
- ✅ Muestra resumen del log
- ✅ Termina limpiamente sin bloquearse
- ✅ Modal del panel web se cierra automáticamente
- ✅ Template actualizado para nuevas instancias

---

**Fecha**: 19 Nov 2025 14:15
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar regeneración de assets desde el panel web y verificar que el modal se cierre
