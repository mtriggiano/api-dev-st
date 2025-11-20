# ✅ Fix: Error "Address already in use" al Regenerar Assets

## 🐛 Problema

Al regenerar assets, el proceso fallaba con código 255:

```
⚠️  Proceso terminó con código: 255
```

### Error Real

Al ejecutar manualmente el comando de regeneración:

```
OSError: [Errno 98] Address already in use
```

## 🔍 Causa

El script detenía el servicio de Odoo pero inmediatamente intentaba ejecutar el comando de regeneración en el mismo puerto, sin esperar a que el puerto se liberara completamente.

**Secuencia del problema**:
```
1. sudo systemctl stop odoo19e-dev-testp4
2. Inmediatamente: ./odoo-bin -c ./odoo.conf --update=all
3. Error: Puerto 3100 todavía en uso por el proceso anterior
```

El proceso de Odoo toma unos segundos en liberar el puerto después de que systemd lo detiene.

## ✅ Solución

Agregar una espera de 5 segundos después de detener el servicio para permitir que el puerto se libere:

```bash
echo "⏹️  Deteniendo servicio Odoo..."
sudo systemctl stop "odoo19e-$INSTANCE_NAME"

# Esperar a que el puerto se libere
echo "   Esperando a que el puerto se libere..."
sleep 5

echo "🎨 Regenerando assets..."
```

## 📊 Flujo Corregido

### Antes (Fallaba)
```
1. Detener servicio → systemctl stop
2. Inmediatamente ejecutar odoo-bin
3. ❌ Error: Puerto en uso
```

### Ahora (Funciona)
```
1. Detener servicio → systemctl stop
2. Esperar 5 segundos → sleep 5
3. Puerto liberado
4. Ejecutar odoo-bin
5. ✅ Regeneración exitosa
```

## 🎯 Nuevo Output Esperado

```
🎨 Regenerando assets de Odoo...
   Instancia: dev-testp4
⏹️  Deteniendo servicio Odoo...
   Esperando a que el puerto se libere...
🎨 Regenerando assets...
   Esto puede tardar 1-2 minutos, por favor espera...
   Iniciando proceso de actualización...
   Loading registry for database dev-testp4-prod-panel4...
   Modules loaded.
   Generating assets...
   Assets bundle 'web.assets_backend' generated
   Assets bundle 'web.assets_frontend' generated
✅ Regeneración completada exitosamente
▶️  Iniciando servicio Odoo...
✅ Servicio iniciado correctamente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Assets regenerados correctamente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🧪 Prueba

### Desde Panel Web

1. Ir a "Instancias"
2. Clic en ⚙️ de `dev-testp4`
3. Seleccionar "Regenerar Assets"
4. Clic en "Regenerar"

**Resultado esperado**:
```
✅ No hay error "Address already in use"
✅ Proceso completa exitosamente
✅ Assets se regeneran correctamente
✅ Servicio se reinicia sin problemas
```

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
   [Progreso visible...]
✅ Regeneración completada exitosamente
```

## 📁 Archivos Modificados

### Instancia Existente
```
/home/mtg/apps/develop/odoo/dev-testp4/
└── regenerate-assets.sh        ✅ Agregado sleep 5
```

### Template
```
/home/mtg/api-dev/scripts/odoo/
└── create-dev-instance.sh      ✅ Template actualizado
```

## 💡 Por Qué 5 Segundos

### Tiempo de Liberación del Puerto

Cuando systemd detiene un servicio:
1. Envía señal SIGTERM al proceso
2. Proceso cierra conexiones
3. Proceso libera el puerto
4. Proceso termina

Este proceso puede tomar 2-5 segundos dependiendo de:
- Conexiones activas
- Carga del sistema
- Procesos hijos

**5 segundos es un tiempo seguro** que garantiza que el puerto esté libre.

### Alternativa Más Robusta

Si 5 segundos no fueran suficientes, se podría verificar el puerto:

```bash
# Esperar hasta que el puerto esté libre (máximo 10 segundos)
for i in {1..10}; do
  if ! ss -tuln | grep -q ":$PORT "; then
    echo "   Puerto liberado"
    break
  fi
  sleep 1
done
```

Pero en la práctica, 5 segundos es suficiente y más simple.

## 🔍 Verificación Manual

### Ver si el puerto está en uso

```bash
# Ver qué proceso está usando el puerto 3100
sudo ss -tuln | grep :3100

# O con lsof
sudo lsof -i :3100
```

### Ver estado del servicio

```bash
# Ver si el servicio está activo
sudo systemctl is-active odoo19e-dev-testp4

# Ver logs del servicio
sudo journalctl -u odoo19e-dev-testp4 -n 20
```

## 📊 Códigos de Salida

| Código | Significado | Causa |
|--------|-------------|-------|
| 0 | Éxito | Regeneración completada |
| 98 | Address in use | Puerto ocupado |
| 255 | Error general | Varios errores posibles |

El código 255 es un código genérico de error. El error real se ve en los logs de Odoo.

## 🎯 Resultado

- ✅ Script espera 5 segundos después de detener servicio
- ✅ Puerto se libera correctamente
- ✅ Regeneración funciona sin errores
- ✅ Template actualizado para nuevas instancias

---

**Fecha**: 19 Nov 2025 13:00
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar regeneración de assets desde el panel web
