# 🔄 Rediseño del Sistema de Backups para Múltiples Instancias

## 📋 Análisis del Sistema Actual

### Limitaciones Identificadas

**1. Diseñado para Una Sola Instancia**
- Hardcodeado para `PROD_INSTANCE_NAME` (una sola producción)
- Crontab único para todas las instancias
- No permite configuración individual por instancia

**2. Sin Control Granular**
- No se puede pausar/activar backup por instancia
- Todas las instancias se respaldan o ninguna
- No hay priorización de instancias

**3. Configuración Global**
- `backup_config.json` es único para todo el sistema
- `retention_days` y `schedule` son globales
- No hay metadata por instancia

**4. Estructura de Archivos**
- Formato: `backup_{PROD_DB}_{TIMESTAMP}.tar.gz`
- No distingue entre instancias fácilmente
- Difícil gestionar múltiples producciones

## 🎯 Propuesta de Rediseño

### Arquitectura Nueva

```
backups/
├── backup_config.json          # Configuración global
├── instances/
│   ├── prod-panel4/
│   │   ├── config.json         # Config específica de instancia
│   │   ├── backup_20251119_030000.tar.gz
│   │   ├── backup_20251119_150000.tar.gz
│   │   └── backup.log
│   ├── cliente1/
│   │   ├── config.json
│   │   ├── backup_20251119_030000.tar.gz
│   │   └── backup.log
│   └── principal/
│       ├── config.json
│       └── backup.log
└── cron.log
```

### Configuración por Instancia

**Archivo**: `backups/instances/{instance_name}/config.json`

```json
{
  "instance_name": "prod-panel4",
  "auto_backup_enabled": true,
  "schedule": "0 3 * * *",
  "retention_days": 7,
  "priority": "high",
  "last_backup": "2025-11-19 03:00:00",
  "last_backup_status": "success",
  "last_backup_size": 1234567890,
  "backup_count": 15,
  "total_size": 12345678900,
  "created_at": "2025-11-01 10:00:00",
  "updated_at": "2025-11-19 03:00:00"
}
```

### Configuración Global

**Archivo**: `backups/backup_config.json`

```json
{
  "global_retention_days": 7,
  "max_backups_per_instance": 30,
  "max_total_size_gb": 100,
  "notification_email": "admin@example.com",
  "instances": {
    "prod-panel4": {
      "auto_backup_enabled": true,
      "schedule": "0 3 * * *",
      "retention_days": 7
    },
    "cliente1": {
      "auto_backup_enabled": true,
      "schedule": "0 4 * * *",
      "retention_days": 14
    },
    "principal": {
      "auto_backup_enabled": false,
      "schedule": "0 2 * * 0",
      "retention_days": 30
    }
  }
}
```

## 🔧 Funcionalidades Nuevas

### 1. Gestión por Instancia

**Activar/Pausar Backup Automático**
```python
backup_manager.toggle_auto_backup(instance_name, enabled=True/False)
```

**Configurar Schedule Individual**
```python
backup_manager.update_instance_config(
    instance_name="prod-panel4",
    schedule="0 3 * * *",  # 3 AM diario
    retention_days=7
)
```

**Prioridades**
- `high`: Backup diario, retención 30 días
- `medium`: Backup diario, retención 14 días
- `low`: Backup semanal, retención 7 días
- `manual`: Solo backups manuales

### 2. Backup Manual por Instancia

```python
backup_manager.create_backup(instance_name="prod-panel4")
```

### 3. Restauración por Instancia

```python
backup_manager.restore_backup(
    instance_name="prod-panel4",
    backup_filename="backup_20251119_030000.tar.gz"
)
```

### 4. Listado Filtrado

```python
# Listar backups de una instancia
backup_manager.list_backups(instance_name="prod-panel4")

# Listar todas las instancias con backups
backup_manager.list_instances_with_backups()

# Estadísticas globales
backup_manager.get_backup_stats()
```

## 📊 Estructura de Datos

### Modelo de Instancia con Backup

```python
{
  "instance_name": "prod-panel4",
  "type": "production",
  "database": "prod-panel4",
  "domain": "panel4.softrigx.com",
  "backup_config": {
    "enabled": true,
    "schedule": "0 3 * * *",
    "retention_days": 7,
    "last_backup": "2025-11-19 03:00:00",
    "last_status": "success",
    "backup_count": 15,
    "total_size_mb": 1234.56
  }
}
```

### Respuesta de Listado

```python
{
  "instances": [
    {
      "name": "prod-panel4",
      "backup_enabled": true,
      "backup_count": 15,
      "last_backup": "2025-11-19 03:00:00",
      "total_size_mb": 1234.56,
      "schedule": "0 3 * * *"
    },
    {
      "name": "cliente1",
      "backup_enabled": true,
      "backup_count": 8,
      "last_backup": "2025-11-19 04:00:00",
      "total_size_mb": 567.89,
      "schedule": "0 4 * * *"
    }
  ],
  "total_backups": 23,
  "total_size_mb": 1802.45
}
```

## 🎨 UI Propuesta

### Panel de Backups Mejorado

```
┌─────────────────────────────────────────────────────────┐
│ Backups de Instancias de Producción                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [Filtrar por instancia ▼] [Buscar...]                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 📦 prod-panel4                                          │
│ ├─ Backup automático: ✅ Activo (3:00 AM diario)       │
│ ├─ Último backup: 19/11/2025 03:00                     │
│ ├─ Backups: 15 (1.2 GB)                                │
│ └─ [⚙️ Configurar] [💾 Backup Manual] [📋 Ver Backups]│
│                                                         │
│ 📦 cliente1                                             │
│ ├─ Backup automático: ✅ Activo (4:00 AM diario)       │
│ ├─ Último backup: 19/11/2025 04:00                     │
│ ├─ Backups: 8 (567 MB)                                 │
│ └─ [⚙️ Configurar] [💾 Backup Manual] [📋 Ver Backups]│
│                                                         │
│ 📦 principal                                            │
│ ├─ Backup automático: ⏸️ Pausado                       │
│ ├─ Último backup: 12/11/2025 02:00                     │
│ ├─ Backups: 4 (234 MB)                                 │
│ └─ [⚙️ Configurar] [💾 Backup Manual] [📋 Ver Backups]│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Modal de Configuración

```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ Configurar Backups - prod-panel4                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Backup Automático                                       │
│ [✓] Activar backups automáticos                        │
│                                                         │
│ Horario                                                 │
│ [0 3 * * *] (3:00 AM todos los días)                   │
│ Presets: [Diario 3AM] [Semanal] [Mensual] [Custom]    │
│                                                         │
│ Retención                                               │
│ [7] días                                                │
│ Presets: [7 días] [14 días] [30 días] [Custom]        │
│                                                         │
│ Prioridad                                               │
│ ○ Alta (diario, 30 días)                               │
│ ● Media (diario, 14 días)                              │
│ ○ Baja (semanal, 7 días)                               │
│ ○ Manual (sin automático)                              │
│                                                         │
│ [Cancelar] [Guardar Configuración]                     │
└─────────────────────────────────────────────────────────┘
```

### Lista de Backups por Instancia

```
┌─────────────────────────────────────────────────────────┐
│ 📋 Backups de prod-panel4                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📦 backup_20251119_030000.tar.gz                    │ │
│ │ 📅 19/11/2025 03:00  📊 123 MB                      │ │
│ │ [⬇️ Descargar] [🔄 Restaurar] [🗑️ Eliminar]        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📦 backup_20251118_030000.tar.gz                    │ │
│ │ 📅 18/11/2025 03:00  📊 121 MB                      │ │
│ │ [⬇️ Descargar] [🔄 Restaurar] [🗑️ Eliminar]        │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ [Página 1 de 3]                                         │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Crontab Dinámico

### Enfoque Actual (Limitado)
```cron
# Odoo Production Backup
0 3 * * * /home/mtg/api-dev/scripts/odoo/backup-production.sh
```

### Enfoque Nuevo (Múltiples Instancias)
```cron
# Odoo Backups - Managed by API-DEV
# prod-panel4
0 3 * * * /home/mtg/api-dev/scripts/odoo/backup-instance.sh prod-panel4 >> /home/mtg/backups/cron.log 2>&1

# cliente1
0 4 * * * /home/mtg/api-dev/scripts/odoo/backup-instance.sh cliente1 >> /home/mtg/backups/cron.log 2>&1

# principal (pausado - comentado)
# 0 2 * * 0 /home/mtg/api-dev/scripts/odoo/backup-instance.sh principal >> /home/mtg/backups/cron.log 2>&1
```

## 📝 Nuevo Script: backup-instance.sh

```bash
#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Script de backup para una instancia específica
INSTANCE_NAME="$1"

if [ -z "$INSTANCE_NAME" ]; then
  echo "❌ Error: Debe especificar el nombre de la instancia"
  echo "Uso: $0 <instance_name>"
  exit 1
fi

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"

# Configuración
BACKUP_BASE_DIR="${BACKUPS_PATH:-/home/mtg/backups}"
INSTANCE_BACKUP_DIR="$BACKUP_BASE_DIR/instances/$INSTANCE_NAME"
CONFIG_FILE="$INSTANCE_BACKUP_DIR/config.json"

# Crear directorio si no existe
mkdir -p "$INSTANCE_BACKUP_DIR"

# Leer configuración de la instancia
if [ -f "$CONFIG_FILE" ]; then
  RETENTION_DAYS=$(jq -r '.retention_days // 7' "$CONFIG_FILE")
  AUTO_ENABLED=$(jq -r '.auto_backup_enabled // true' "$CONFIG_FILE")
else
  RETENTION_DAYS=7
  AUTO_ENABLED=true
fi

# Verificar si el backup automático está habilitado
if [ "$AUTO_ENABLED" != "true" ]; then
  echo "⏸️  Backup automático deshabilitado para $INSTANCE_NAME"
  exit 0
fi

# Obtener información de la instancia
DB_NAME="$INSTANCE_NAME"
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
FILESTORE_PATH="$FILESTORE_BASE/$DB_NAME"

# Timestamp
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_PATH="$INSTANCE_BACKUP_DIR/$BACKUP_NAME"

echo "💾 Iniciando backup de $INSTANCE_NAME..."
echo "   Timestamp: $TIMESTAMP"

# Crear directorio temporal
mkdir -p "$BACKUP_PATH"

# 1. Backup de base de datos
echo "🗄️  Creando dump de base de datos..."
sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_PATH/dump.sql"
DB_SIZE=$(du -h "$BACKUP_PATH/dump.sql" | cut -f1)
echo "✅ Base de datos: $DB_SIZE"

# 2. Copiar filestore
if [ -d "$FILESTORE_PATH" ]; then
  echo "📁 Copiando filestore..."
  cp -r "$FILESTORE_PATH" "$BACKUP_PATH/filestore"
  FILE_COUNT=$(find "$BACKUP_PATH/filestore" -type f | wc -l)
  FS_SIZE=$(du -sh "$BACKUP_PATH/filestore" | cut -f1)
  echo "✅ Filestore: $FS_SIZE ($FILE_COUNT archivos)"
else
  echo "⚠️  No se encontró filestore"
  mkdir -p "$BACKUP_PATH/filestore"
fi

# 3. Comprimir
echo "📦 Creando archivo tar.gz..."
cd "$INSTANCE_BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" -C "$BACKUP_NAME" .
rm -rf "$BACKUP_PATH"

TOTAL_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
echo "✅ Backup completado: ${BACKUP_NAME}.tar.gz ($TOTAL_SIZE)"

# 4. Limpiar backups antiguos
echo "🧹 Limpiando backups antiguos (retención: $RETENTION_DAYS días)..."
find "$INSTANCE_BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 "$INSTANCE_BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)
echo "✅ Backups restantes: $REMAINING"

# 5. Actualizar configuración
if [ -f "$CONFIG_FILE" ]; then
  # Actualizar last_backup y estadísticas
  BACKUP_SIZE=$(stat -f%z "${BACKUP_NAME}.tar.gz" 2>/dev/null || stat -c%s "${BACKUP_NAME}.tar.gz")
  jq --arg date "$(date '+%Y-%m-%d %H:%M:%S')" \
     --arg status "success" \
     --arg size "$BACKUP_SIZE" \
     --arg count "$REMAINING" \
     '.last_backup = $date | .last_backup_status = $status | .last_backup_size = ($size | tonumber) | .backup_count = ($count | tonumber)' \
     "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
fi

# 6. Registrar en log
LOG_FILE="$INSTANCE_BACKUP_DIR/backup.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup: ${BACKUP_NAME}.tar.gz - Size: $TOTAL_SIZE - Status: OK" >> "$LOG_FILE"

echo "✅ Backup completado exitosamente"
```

## 🔌 API Endpoints Nuevos

### Gestión de Configuración

```
GET    /api/backup/instances                    # Listar instancias con config
GET    /api/backup/instances/{name}/config      # Config de instancia
PUT    /api/backup/instances/{name}/config      # Actualizar config
POST   /api/backup/instances/{name}/toggle      # Activar/pausar
```

### Backups por Instancia

```
GET    /api/backup/instances/{name}/backups     # Listar backups
POST   /api/backup/instances/{name}/backup      # Crear backup manual
POST   /api/backup/instances/{name}/restore     # Restaurar backup
DELETE /api/backup/instances/{name}/backups/{file}  # Eliminar backup
```

### Estadísticas

```
GET    /api/backup/stats                        # Estadísticas globales
GET    /api/backup/instances/{name}/stats       # Estadísticas de instancia
```

## 📊 Plan de Migración

### Fase 1: Preparación (Sin Romper Nada)
1. ✅ Crear nueva estructura de directorios
2. ✅ Implementar `BackupManagerV2` (paralelo al actual)
3. ✅ Crear script `backup-instance.sh`
4. ✅ Mantener compatibilidad con sistema actual

### Fase 2: Migración de Datos
1. ✅ Migrar backups existentes a nueva estructura
2. ✅ Crear configs por instancia
3. ✅ Actualizar crontab gradualmente

### Fase 3: Nuevo Frontend
1. ✅ Implementar nuevo panel de backups
2. ✅ Mantener panel antiguo como fallback
3. ✅ Testing exhaustivo

### Fase 4: Activación
1. ✅ Cambiar a `BackupManagerV2`
2. ✅ Deprecar sistema antiguo
3. ✅ Documentar cambios

## 🎯 Beneficios del Rediseño

### Para el Usuario
- ✅ Control granular por instancia
- ✅ Pausar/activar backups fácilmente
- ✅ Configuración individual de horarios
- ✅ Mejor organización de archivos
- ✅ Estadísticas por instancia

### Para el Sistema
- ✅ Escalable a N instancias
- ✅ Mejor gestión de recursos
- ✅ Logs separados por instancia
- ✅ Configuración más flexible
- ✅ Fácil mantenimiento

### Para el Administrador
- ✅ Visibilidad clara del estado
- ✅ Control fino de retención
- ✅ Priorización de instancias
- ✅ Alertas por instancia
- ✅ Auditoría mejorada

## 📋 Checklist de Implementación

### Backend
- [ ] Crear `BackupManagerV2` con soporte multi-instancia
- [ ] Implementar gestión de configuración por instancia
- [ ] Crear endpoints nuevos
- [ ] Migrar datos existentes
- [ ] Testing exhaustivo

### Scripts
- [ ] Crear `backup-instance.sh`
- [ ] Actualizar `restore-production.sh` para multi-instancia
- [ ] Script de migración de backups
- [ ] Actualizar crontab manager

### Frontend
- [ ] Rediseñar componente Backups
- [ ] Agregar filtros por instancia
- [ ] Modal de configuración por instancia
- [ ] Vista de backups por instancia
- [ ] Indicadores de estado

### Documentación
- [ ] Guía de migración
- [ ] API documentation
- [ ] User guide
- [ ] Admin guide

## 🔮 Funcionalidades Futuras

### Notificaciones
- Email al completar backup
- Alertas si falla backup
- Resumen semanal

### Backup Remoto
- Subir a S3/Cloud Storage
- Backup offsite automático
- Replicación geográfica

### Snapshots
- Backups incrementales
- Snapshots de filesystem
- Backup diferencial

### Monitoreo
- Dashboard de salud
- Métricas de performance
- Alertas proactivas

---

**Fecha**: 19 Nov 2025 15:00
**Estado**: 📋 PROPUESTA
**Próximo paso**: Revisar propuesta y comenzar implementación
