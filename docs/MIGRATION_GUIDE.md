# 📋 Guía de Migración - Sistema API-DEV

## 🔄 Migración desde la Estructura Antigua

Esta guía te ayudará a migrar desde la estructura antigua del proyecto a la nueva estructura refactorizada.

## 📊 Cambios Principales

### 1. Estructura de Carpetas

**Antes:**
```
/home/go/
├── api/                    # Carpeta del proyecto
├── scripts/                # Scripts separados
├── dev-instances.txt       # Archivos dispersos
└── puertos_ocupados_odoo.txt
```

**Ahora:**
```
/home/go/
└── api-dev/                # Todo centralizado
    ├── scripts/            # Scripts dentro del proyecto
    ├── data/               # Archivos de estado
    └── .env                # Configuración centralizada
```

### 2. Configuración

**Antes:** Credenciales hardcodeadas en cada script
```bash
DB_PASSWORD="!Phax3312!IMAC"
CF_API_TOKEN="JK1cCBg776SHiZX9T6Ky5b2gtjMkpUsNHxVyQ0Vs"
```

**Ahora:** Todo en archivo `.env`
```bash
# Configuración centralizada y segura
DB_PASSWORD=${DB_PASSWORD}
CF_API_TOKEN=${CF_API_TOKEN}
```

### 3. Scripts

**Ubicación anterior:**
- `/home/go/scripts/`
- `/home/go/api/script/Init Instasnce (Danger Jhon)/`

**Nueva ubicación:**
- `/home/go/api-dev/scripts/odoo/`
- `/home/go/api-dev/scripts/utils/`

**Nombres actualizados:**
- `start-odoo19e-instance.sh` → `init-production.sh`
- `remove-odooe-instance.sh` → `remove-production.sh`

## 🚀 Pasos de Migración

### Paso 1: Backup Completo

```bash
# Crear backup del sistema actual
cd /home/go
tar -czf backup_sistema_$(date +%Y%m%d).tar.gz \
    api/ scripts/ dev-instances.txt puertos_ocupados_odoo.txt \
    apps/ backups/ 2>/dev/null || true
```

### Paso 2: Clonar el Repositorio Actualizado

```bash
# Si ya tienes el repo clonado
cd /home/go/api-dev
git pull origin main

# Si es una instalación nueva
cd /home/go
git clone [URL_DEL_REPO] api-dev
cd api-dev
```

### Paso 3: Ejecutar Quickstart

```bash
cd /home/go/api-dev
./quickstart.sh
```

Durante el quickstart:
1. **Detectará** configuraciones existentes (ej: instancia `imac-production`)
2. **Preguntará** si deseas mantener los valores actuales
3. **Importará** las credenciales que ingreses
4. **Generará** el archivo `.env` con toda la configuración

### Paso 4: Migrar Archivos de Estado

```bash
# Los archivos ya fueron movidos automáticamente durante la reorganización
# Verificar que existen en la nueva ubicación:
ls -la /home/go/api-dev/data/
```

### Paso 5: Actualizar Referencias

Si tienes scripts personalizados o cron jobs, actualiza las rutas:

**Cron jobs antiguos:**
```bash
0 2 * * * /home/go/scripts/backup-production.sh
```

**Cron jobs nuevos:**
```bash
0 2 * * * /home/go/api-dev/scripts/odoo/backup-production.sh
```

### Paso 6: Verificar Configuración

```bash
# Cargar y validar variables de entorno
source scripts/utils/validate-env.sh --full
```

### Paso 7: Probar Scripts

```bash
# Probar backup (no destructivo)
./scripts/odoo/backup-production.sh

# Listar instancias
ls /home/go/apps/production/odoo/
ls /home/go/apps/develop/odoo/
```

## ⚠️ Consideraciones Importantes

### Instancia de Producción

Si tu instancia actual se llama `imac-production`:
- El quickstart te preguntará si deseas mantener ese nombre
- Puedes cambiarlo a `odoo-production` (recomendado)
- O mantener el nombre actual para compatibilidad

### Base de Datos

Las bases de datos existentes **NO se modifican**. Los scripts actualizados:
- Detectan automáticamente las BD existentes
- Mantienen compatibilidad con nombres antiguos
- Usan los nuevos nombres para nuevas instalaciones

### Permisos

```bash
# Asegurar permisos correctos
chmod 600 /home/go/api-dev/.env
chmod +x /home/go/api-dev/scripts/odoo/*.sh
chmod +x /home/go/api-dev/scripts/utils/*.sh
```

## 🔍 Verificación Post-Migración

### Checklist de Verificación

- [ ] El archivo `.env` existe y tiene las credenciales correctas
- [ ] Los scripts en `scripts/odoo/` son ejecutables
- [ ] Los archivos de datos están en `data/`
- [ ] El panel de control se despliega correctamente
- [ ] Los backups funcionan
- [ ] Se pueden crear nuevas instancias de desarrollo

### Comandos de Verificación

```bash
# 1. Verificar estructura
tree -L 2 /home/go/api-dev/

# 2. Verificar variables de entorno
grep -E "^(DB_PASSWORD|CF_API_TOKEN|DOMAIN_ROOT)" .env

# 3. Verificar servicios
sudo systemctl status server-panel-api
sudo systemctl status nginx

# 4. Verificar instancias Odoo
sudo systemctl status odoo19e-*
```

## 🆘 Solución de Problemas

### Error: "No se encontró el archivo .env"

```bash
# Ejecutar quickstart para generar .env
cd /home/go/api-dev
./quickstart.sh
```

### Error: "Variable X no está definida"

```bash
# Editar .env y agregar la variable faltante
nano /home/go/api-dev/.env

# Verificar nuevamente
source scripts/utils/validate-env.sh
```

### Error: "No se puede conectar a PostgreSQL"

```bash
# Verificar credenciales en .env
grep DB_ .env

# Probar conexión manualmente
PGPASSWORD=tu_password psql -h localhost -U go -d postgres -c '\l'
```

### Scripts no encuentran las rutas

```bash
# Verificar que PROJECT_ROOT esté definido
echo $PROJECT_ROOT

# Si no está definido, cargar variables
source /home/go/api-dev/scripts/utils/load-env.sh
```

## 📝 Notas Finales

### Ventajas de la Nueva Estructura

✅ **Seguridad**: Credenciales centralizadas y protegidas  
✅ **Portabilidad**: Fácil despliegue en nuevos servidores  
✅ **Mantenibilidad**: Una sola fuente de configuración  
✅ **Git-friendly**: `.env` no se versiona, `.env.example` sí  
✅ **Organización**: Todo en un solo directorio  

### Rollback (Si es Necesario)

Si necesitas volver a la estructura anterior:

```bash
# Restaurar desde backup
cd /home/go
tar -xzf backup_sistema_[fecha].tar.gz

# Volver a usar scripts antiguos
cd /home/go/api
git checkout [commit_anterior]
```

## 📞 Soporte

Si encuentras problemas durante la migración:

1. Revisa los logs: `sudo journalctl -xe`
2. Verifica el archivo de migración: `cat /home/go/api-dev/MIGRATION_STATE.md`
3. Consulta la documentación: `docs/`

---

**Última actualización**: $(date)
**Versión**: 2.0.0 (Refactorizada)
