# 🧪 Guía de Testing - Sistema de Backups V2

## ✅ Implementación Completada

### Backend ✅
- [x] BackupManagerV2 con soporte multi-instancia
- [x] Scripts backup-instance.sh y restore-instance.sh
- [x] 13 endpoints API REST
- [x] Integración con Flask
- [x] Logging y auditoría

### Frontend ✅
- [x] Componente BackupsV2.jsx
- [x] Modales de configuración, lista y restauración
- [x] Integración con API
- [x] Ruta /backups-v2 agregada
- [x] Enlace en menú lateral

### Scripts ✅
- [x] Script de migración de backups antiguos
- [x] Actualización automática de crontab

## 🚀 Pasos para Activar el Sistema

### 1. Migrar Backups Existentes (Opcional)

Si tienes backups del sistema antiguo:

```bash
cd /home/mtg/api-dev
sudo ./scripts/utils/migrate-backups-to-v2.sh
```

Esto:
- Moverá backups antiguos a la nueva estructura
- Creará configuraciones para cada instancia
- Dejará los backups automáticos DESHABILITADOS por defecto

### 2. Reiniciar Frontend

```bash
# Si usas npm/yarn
cd /home/mtg/api-dev/frontend
npm run build  # o yarn build

# Si usas un servidor de desarrollo
npm run dev
```

### 3. Verificar Backend

El backend ya fue recargado, pero puedes verificar:

```bash
# Ver logs del backend
sudo journalctl -u api-dev -n 50 -f

# O si usas gunicorn directamente
ps aux | grep gunicorn | grep api-dev
```

## 🧪 Plan de Testing

### Test 1: Acceso al Panel ✅

**Objetivo**: Verificar que el nuevo panel es accesible

**Pasos**:
1. Acceder a https://api-dev.softrigx.com/backups-v2
2. Verificar que carga sin errores
3. Verificar que aparece el menú "Backups V2" en el sidebar

**Resultado esperado**:
- Panel carga correctamente
- Muestra lista de instancias (puede estar vacía)
- No hay errores en consola

---

### Test 2: Listar Instancias ✅

**Objetivo**: Verificar que lista las instancias de producción

**Pasos**:
1. Desde el panel, verificar que aparecen las instancias
2. Verificar que muestra estadísticas (último backup, cantidad, tamaño)
3. Verificar que muestra el estado (Activo/Pausado)

**Resultado esperado**:
- Lista todas las instancias de producción
- Muestra estadísticas correctas
- Estado inicial: Pausado (si es primera vez)

**API Test**:
```bash
curl -X GET http://localhost:5000/api/backup/v2/instances \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Test 3: Configurar Instancia ✅

**Objetivo**: Configurar backup automático para una instancia

**Pasos**:
1. Click en "Configurar" de una instancia
2. Activar checkbox "Activar backups automáticos"
3. Seleccionar horario (ej: Diario 3:00 AM)
4. Configurar retención (ej: 7 días)
5. Seleccionar prioridad (ej: Media)
6. Click en "Guardar"

**Resultado esperado**:
- Modal se cierra
- Toast de confirmación
- Instancia muestra estado "Activo"
- Horario visible en la tarjeta

**API Test**:
```bash
curl -X PUT http://localhost:5000/api/backup/v2/instances/prod-panel4/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_backup_enabled": true,
    "schedule": "0 3 * * *",
    "retention_days": 7,
    "priority": "medium"
  }' | jq
```

---

### Test 4: Activar/Pausar Backup ✅

**Objetivo**: Toggle del backup automático

**Pasos**:
1. Click en "Pausar" de una instancia activa
2. Verificar que cambia a "Pausado"
3. Click en "Activar"
4. Verificar que cambia a "Activo"

**Resultado esperado**:
- Estado cambia inmediatamente
- Toast de confirmación
- Crontab se actualiza

**API Test**:
```bash
# Pausar
curl -X POST http://localhost:5000/api/backup/v2/instances/prod-panel4/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq

# Activar
curl -X POST http://localhost:5000/api/backup/v2/instances/prod-panel4/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}' | jq
```

---

### Test 5: Crear Backup Manual ✅

**Objetivo**: Crear un backup manualmente

**Pasos**:
1. Click en "Backup Manual" de una instancia
2. Esperar mensaje de confirmación
3. Esperar 30-60 segundos
4. Refrescar la página
5. Verificar que aumentó el contador de backups

**Resultado esperado**:
- Botón muestra "Creando..." con spinner
- Toast: "Backup de [instancia] iniciado"
- Después de ~1 min, aparece nuevo backup
- Estadísticas actualizadas

**API Test**:
```bash
# Crear backup
curl -X POST http://localhost:5000/api/backup/v2/instances/prod-panel4/backup \
  -H "Authorization: Bearer $TOKEN" | jq

# Ver log (después de 30 seg)
curl -X GET http://localhost:5000/api/backup/v2/instances/prod-panel4/backup-log \
  -H "Authorization: Bearer $TOKEN" | jq -r '.log'
```

**Verificar en servidor**:
```bash
# Ver backups creados
ls -lh /home/mtg/backups/instances/prod-panel4/

# Ver log del backup
cat /tmp/odoo-backup-prod-panel4-latest.log
```

---

### Test 6: Listar Backups ✅

**Objetivo**: Ver lista de backups de una instancia

**Pasos**:
1. Click en "Ver Backups (N)" de una instancia
2. Verificar que abre modal con lista
3. Verificar que muestra fecha, tamaño
4. Verificar botones: Descargar, Restaurar, Eliminar

**Resultado esperado**:
- Modal muestra lista de backups
- Ordenados por fecha (más reciente primero)
- Información correcta de cada backup

**API Test**:
```bash
curl -X GET http://localhost:5000/api/backup/v2/instances/prod-panel4/backups \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Test 7: Descargar Backup ✅

**Objetivo**: Descargar un backup

**Pasos**:
1. En la lista de backups, click en icono de descarga
2. Verificar que inicia descarga
3. Verificar que el archivo se descarga correctamente

**Resultado esperado**:
- Descarga inicia inmediatamente
- Archivo .tar.gz descargado
- Tamaño correcto

**API Test**:
```bash
# Listar para obtener nombre de archivo
BACKUP_FILE=$(curl -s -X GET http://localhost:5000/api/backup/v2/instances/prod-panel4/backups \
  -H "Authorization: Bearer $TOKEN" | jq -r '.backups[0].filename')

# Descargar
curl -X GET "http://localhost:5000/api/backup/v2/instances/prod-panel4/backups/$BACKUP_FILE/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o "/tmp/$BACKUP_FILE"

# Verificar
ls -lh "/tmp/$BACKUP_FILE"
tar -tzf "/tmp/$BACKUP_FILE" | head
```

---

### Test 8: Eliminar Backup ✅

**Objetivo**: Eliminar un backup antiguo

**Pasos**:
1. En la lista de backups, click en icono de eliminar
2. Confirmar en el prompt
3. Verificar que desaparece de la lista

**Resultado esperado**:
- Prompt de confirmación
- Backup eliminado
- Lista actualizada
- Toast de confirmación

**API Test**:
```bash
BACKUP_FILE="backup_20251119_030000.tar.gz"

curl -X DELETE "http://localhost:5000/api/backup/v2/instances/prod-panel4/backups/$BACKUP_FILE" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Test 9: Restaurar Backup ⚠️ CUIDADO

**Objetivo**: Restaurar un backup (SOLO EN INSTANCIA DE TEST)

**⚠️ ADVERTENCIA**: Esto sobrescribirá la base de datos y filestore actuales

**Pasos**:
1. **SOLO en instancia de test/desarrollo**
2. En la lista de backups, click en icono de restaurar
3. Leer advertencia en modal
4. Click en "Confirmar Restauración"
5. Esperar 2-5 minutos
6. Verificar que la instancia se reinició

**Resultado esperado**:
- Modal de advertencia clara
- Proceso de restauración inicia
- Servicio se detiene y reinicia
- Base de datos y filestore restaurados

**API Test** (SOLO EN TEST):
```bash
BACKUP_FILE="backup_20251119_030000.tar.gz"

curl -X POST http://localhost:5000/api/backup/v2/instances/dev-test/restore \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"$BACKUP_FILE\"}" | jq

# Ver log (después de 2 min)
curl -X GET http://localhost:5000/api/backup/v2/instances/dev-test/restore-log \
  -H "Authorization: Bearer $TOKEN" | jq -r '.log'
```

---

### Test 10: Verificar Crontab ✅

**Objetivo**: Verificar que el crontab se actualiza correctamente

**Pasos**:
1. Activar backup automático en una instancia
2. Verificar crontab del usuario

**Comando**:
```bash
crontab -l | grep "backup-instance.sh"
```

**Resultado esperado**:
```
# Odoo Backups - Managed by API-DEV
0 3 * * * /home/mtg/api-dev/scripts/odoo/backup-instance.sh prod-panel4 >> /home/mtg/backups/cron.log 2>&1
```

---

### Test 11: Estadísticas Globales ✅

**Objetivo**: Ver estadísticas de todos los backups

**API Test**:
```bash
curl -X GET http://localhost:5000/api/backup/v2/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

**Resultado esperado**:
```json
{
  "total_instances": 3,
  "enabled_instances": 2,
  "disabled_instances": 1,
  "total_backups": 23,
  "total_size_gb": 5.67,
  "total_size_human": "5.67 GB",
  "instances": [...]
}
```

---

### Test 12: Búsqueda y Filtros ✅

**Objetivo**: Filtrar instancias en el panel

**Pasos**:
1. En el buscador, escribir parte del nombre de una instancia
2. Verificar que filtra correctamente
3. Borrar búsqueda
4. Verificar que muestra todas nuevamente

**Resultado esperado**:
- Filtrado en tiempo real
- Solo muestra instancias que coinciden
- Sin errores

---

## 🐛 Troubleshooting

### Error: "Script de backup no encontrado"

**Causa**: El script backup-instance.sh no existe o no tiene permisos

**Solución**:
```bash
chmod +x /home/mtg/api-dev/scripts/odoo/backup-instance.sh
```

### Error: "Permission denied" al crear backup

**Causa**: Permisos incorrectos en directorio de backups

**Solución**:
```bash
sudo chown -R mtg:mtg /home/mtg/backups
chmod -R 755 /home/mtg/backups
```

### Error: "Database does not exist"

**Causa**: El nombre de la instancia no coincide con la base de datos

**Solución**:
Verificar que el nombre de la instancia es correcto:
```bash
sudo -u postgres psql -l | grep prod
```

### Backup no aparece después de crearlo

**Causa**: El backup está en progreso o falló

**Solución**:
```bash
# Ver log del backup
cat /tmp/odoo-backup-[instancia]-latest.log

# Ver si el proceso está corriendo
ps aux | grep backup-instance.sh
```

### Crontab no se actualiza

**Causa**: Error en permisos o sintaxis

**Solución**:
```bash
# Ver logs de cron
grep CRON /var/log/syslog | tail -20

# Actualizar manualmente
crontab -e
```

---

## 📊 Checklist de Testing

### Backend
- [ ] Endpoints responden correctamente
- [ ] Autenticación JWT funciona
- [ ] Solo usuarios admin tienen acceso
- [ ] Logs se registran en ActionLog
- [ ] Errores se manejan correctamente

### Scripts
- [ ] backup-instance.sh crea backups
- [ ] restore-instance.sh restaura correctamente
- [ ] Permisos de archivos correctos
- [ ] Logs detallados y claros

### Frontend
- [ ] Panel carga sin errores
- [ ] Modales funcionan correctamente
- [ ] Botones responden
- [ ] Toasts aparecen
- [ ] Estados se actualizan
- [ ] Búsqueda funciona
- [ ] Responsive design

### Integración
- [ ] API y frontend se comunican
- [ ] Crontab se actualiza automáticamente
- [ ] Backups se crean correctamente
- [ ] Restauración funciona
- [ ] Estadísticas son precisas

---

## 🎯 Testing Recomendado

### Orden Sugerido

1. ✅ **Acceso al panel** - Verificar que todo carga
2. ✅ **Listar instancias** - Ver que detecta las instancias
3. ✅ **Configurar instancia** - Activar backup en una instancia de test
4. ✅ **Crear backup manual** - Probar creación manual
5. ✅ **Listar backups** - Ver que aparece el backup creado
6. ✅ **Descargar backup** - Verificar que se puede descargar
7. ✅ **Verificar crontab** - Confirmar que se actualizó
8. ⏰ **Esperar backup automático** - Dejar que cron ejecute (al horario configurado)
9. ⚠️ **Restaurar backup** - SOLO en instancia de test
10. ✅ **Eliminar backup** - Limpiar backups antiguos

### Instancias Recomendadas para Testing

**Para pruebas seguras**:
- Crear una instancia de desarrollo específica para testing
- NO usar instancias de producción para probar restauración

**Comando para crear instancia de test**:
```bash
# Crear instancia de test basada en producción
cd /home/mtg/api-dev/scripts/odoo
sudo ./create-dev-instance.sh
# Nombre: backup-test
# Producción: [tu instancia de prod]
```

---

## 📝 Notas Finales

### Compatibilidad
- ✅ Sistema antiguo sigue funcionando
- ✅ Backups en formato Odoo Online
- ✅ Migración no destructiva

### Seguridad
- ✅ Solo usuarios admin
- ✅ JWT requerido en todos los endpoints
- ✅ Validación de nombres de archivo
- ✅ Logs de auditoría

### Performance
- ✅ Backups en background
- ✅ No bloquea la UI
- ✅ Actualización cada 30 segundos
- ✅ Limpieza automática de backups antiguos

---

**Fecha**: 19 Nov 2025 15:45
**Estado**: ✅ LISTO PARA TESTING
**Próximo paso**: Ejecutar plan de testing
