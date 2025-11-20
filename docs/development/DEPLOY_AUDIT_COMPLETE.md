# 🔍 AUDITORÍA COMPLETA - deploy.sh
## Sistema API-DEV - Todos los Módulos

**Fecha**: 2025-11-02  
**Objetivo**: Verificar que `deploy.sh` configure correctamente TODOS los módulos del sistema

---

## 📊 MÓDULOS DEL SISTEMA

### 1. **Autenticación (Auth)**
- **Ruta**: `/api/auth`
- **Archivo**: `backend/routes/auth.py`
- **Dependencias**:
  - ✅ Flask-JWT-Extended
  - ✅ bcrypt
  - ✅ PostgreSQL (tabla `users`)
  - ✅ SECRET_KEY y JWT_SECRET_KEY

### 2. **Métricas del Sistema**
- **Ruta**: `/api/metrics`
- **Archivo**: `backend/routes/metrics.py`
- **Dependencias**:
  - ✅ psutil
  - ✅ PostgreSQL (tabla `metrics_history`)
  - ✅ Cron job para guardar métricas cada minuto

### 3. **Gestión de Instancias Odoo**
- **Ruta**: `/api/instances`
- **Archivo**: `backend/routes/instances.py`
- **Dependencias**:
  - ✅ Scripts de Odoo en `/scripts/odoo/`
  - ✅ Archivos de datos: `puertos_ocupados_odoo.txt`, `dev-instances.txt`
  - ✅ Directorios: `PROD_ROOT`, `DEV_ROOT`
  - ✅ PostgreSQL (tabla `action_logs`)
  - ✅ Permisos sudo para systemctl

### 4. **Logs y Auditoría**
- **Ruta**: `/api/logs`
- **Archivo**: `backend/routes/logs.py`
- **Dependencias**:
  - ✅ PostgreSQL (tabla `action_logs`)
  - ✅ Relación con tabla `users`

### 5. **Backups y Restauración**
- **Ruta**: `/api/backup`
- **Archivo**: `backend/routes/backup.py`
- **Dependencias**:
  - ✅ Scripts: `backup-production.sh`, `restore-production.sh`
  - ✅ Directorio: `BACKUPS_PATH` (/home/go/backups)
  - ✅ Nginx: client_max_body_size 1024M
  - ✅ Gunicorn: timeout 600s
  - ✅ PostgreSQL para logs

### 6. **Integración GitHub**
- **Ruta**: `/api/github`
- **Archivo**: `backend/routes/github.py`
- **Dependencias**:
  - ✅ Git instalado en el sistema
  - ✅ requests (para GitHub API)
  - ✅ PostgreSQL (tabla `github_configs`)
  - ✅ Acceso a directorios de instancias

### 7. **Carga de Archivos (Chunked Upload)**
- **Ruta**: `/api/chunked-upload`
- **Archivo**: `backend/routes/chunked_upload.py`
- **Dependencias**:
  - ✅ Directorio temporal para chunks
  - ✅ Flask MAX_CONTENT_LENGTH
  - ✅ Nginx proxy_buffering off

---

## 🗄️ BASE DE DATOS - Tablas Requeridas

### Tablas que deben crearse automáticamente:
1. ✅ `users` - Usuarios del sistema
2. ✅ `action_logs` - Logs de acciones
3. ✅ `github_configs` - Configuraciones de GitHub
4. ✅ `metrics_history` - Historial de métricas

**Estado**: Se crean automáticamente con `init_db(app)` en deploy.sh ✅

---

## 📁 ESTRUCTURA DE DIRECTORIOS REQUERIDA

### Directorios que DEBE crear deploy.sh:

| Directorio | Propósito | Estado Actual |
|------------|-----------|---------------|
| `/home/go/api-dev/logs` | Logs de Gunicorn | ✅ CREADO (línea 92) |
| `/home/go/api-dev/data` | Archivos de datos | ✅ CREADO (línea 93) |
| `/home/go/backups` | Backups de Odoo | ✅ CREADO (línea 94) |
| `/home/go/apps/production/odoo` | Instancias producción | ⚠️ NO SE CREA |
| `/home/go/apps/develop/odoo` | Instancias desarrollo | ⚠️ NO SE CREA |

### Archivos que DEBE crear deploy.sh:

| Archivo | Propósito | Estado Actual |
|---------|-----------|---------------|
| `data/puertos_ocupados_odoo.txt` | Puertos en uso | ✅ CREADO (línea 95) |
| `data/dev-instances.txt` | Registro de instancias dev | ✅ CREADO (línea 96) |

---

## 🔧 DEPENDENCIAS DEL SISTEMA

### Comandos que DEBEN estar instalados:

| Comando | Usado por | Verificado en deploy.sh |
|---------|-----------|-------------------------|
| `python3.12` | Backend | ✅ Línea 46 |
| `node` | Frontend | ✅ Línea 47 |
| `npm` | Frontend | ✅ Línea 47 |
| `nginx` | Web server | ✅ Línea 48 |
| `psql` | PostgreSQL | ❌ NO |
| `pg_dump` | Backups | ❌ NO |
| `git` | GitHub integration | ❌ NO |
| `jq` | Scripts Odoo | ❌ NO |
| `curl` | API calls | ❌ NO |
| `certbot` | SSL | ❌ NO |

---

## 🐍 DEPENDENCIAS PYTHON

### requirements.txt - Estado:

```python
Flask==3.0.0                    ✅
Flask-CORS==4.0.0              ✅
Flask-JWT-Extended==4.6.0      ✅
Flask-SQLAlchemy==3.1.1        ✅
psycopg2-binary==2.9.9         ✅
python-dotenv==1.0.0           ✅
psutil==5.9.6                  ✅
gunicorn==21.2.0               ✅
bcrypt==4.1.1                  ✅
requests==2.31.0               ✅
```

**Estado**: Todas las dependencias necesarias están en requirements.txt ✅

---

## ⚙️ CONFIGURACIÓN DE SERVICIOS

### 1. Servicio Systemd (server-panel-api)

**Configuración Actual** (líneas 106-148):
```ini
[Unit]
Description=Server Panel API
After=network.target postgresql.service  ✅
Wants=postgresql.service                 ✅

[Service]
Type=simple
User=$USER                               ✅
WorkingDirectory=$BACKEND_DIR            ✅
Environment="PATH=$BACKEND_DIR/venv/bin" ✅

ExecStart=gunicorn \
    -w 4 \                               ✅
    --timeout 600 \                      ✅
    --max-requests 1000 \                ✅
    --access-logfile logs/gunicorn-access.log ✅
    --error-logfile logs/gunicorn-error.log   ✅
    wsgi:app

Restart=always                           ✅
RestartSec=10                            ✅

LimitNOFILE=65536                        ✅
LimitNPROC=4096                          ✅
```

**Estado**: ✅ COMPLETO Y CORRECTO

---

### 2. Nginx

**Configuración Actual** (líneas 179-220):
```nginx
server {
    listen 80;
    server_name $DOMAIN;
    
    # Archivos grandes
    client_max_body_size 1024M;          ✅
    client_body_timeout 600s;            ✅
    client_header_timeout 600s;          ✅
    
    # Frontend
    location / {
        root $FRONTEND_DIR/dist;         ✅
        try_files $uri $uri/ /index.html; ✅
    }
    
    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:5000; ✅
        proxy_connect_timeout 600s;       ✅
        proxy_send_timeout 600s;          ✅
        proxy_read_timeout 600s;          ✅
        proxy_buffering off;              ✅
        proxy_request_buffering off;      ✅
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000; ✅
    }
}
```

**Estado**: ✅ COMPLETO Y CORRECTO

---

### 3. Cron Job para Métricas

**Configuración Actual** (líneas 242-244):
```bash
CRON_JOB="* * * * * curl -X POST http://localhost:5000/api/metrics/save >/dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "/api/metrics/save"; echo "$CRON_JOB") | crontab -
```

**Estado**: ✅ CORRECTO

---

## 🔐 VARIABLES DE ENTORNO REQUERIDAS

### Variables que DEBE tener el .env:

| Variable | Usado por | Crítico |
|----------|-----------|---------|
| `SECRET_KEY` | Flask sessions | 🔴 SÍ |
| `JWT_SECRET_KEY` | JWT tokens | 🔴 SÍ |
| `DB_USER` | PostgreSQL | 🔴 SÍ |
| `DB_PASSWORD` | PostgreSQL | 🔴 SÍ |
| `DB_HOST` | PostgreSQL | 🟡 No (default: localhost) |
| `DB_PORT` | PostgreSQL | 🟡 No (default: 5432) |
| `DB_NAME` | PostgreSQL | 🟡 No (default: server_panel) |
| `API_DOMAIN` | Nginx, CORS | 🔴 SÍ |
| `CF_API_TOKEN` | Cloudflare DNS | 🔴 SÍ |
| `DOMAIN_ROOT` | DNS, Cloudflare | 🔴 SÍ |
| `PUBLIC_IP` | DNS A record | 🔴 SÍ |
| `PROD_ROOT` | Instancias producción | 🔴 SÍ |
| `DEV_ROOT` | Instancias desarrollo | 🔴 SÍ |
| `SCRIPTS_PATH` | Scripts Odoo | 🔴 SÍ |
| `DATA_PATH` | Archivos de datos | 🔴 SÍ |
| `BACKUPS_PATH` | Backups | 🔴 SÍ |
| `PUERTOS_FILE` | Gestión de puertos | 🔴 SÍ |
| `DEV_INSTANCES_FILE` | Registro instancias | 🔴 SÍ |
| `ODOO_ADMIN_PASSWORD` | Odoo admin | 🔴 SÍ |
| `PROD_INSTANCE_NAME` | Nombre producción | 🔴 SÍ |
| `PYTHON_BIN` | Python path | 🟡 No (default: /usr/bin/python3.12) |
| `SYSTEM_USER` | Usuario del sistema | 🟡 No (default: go) |
| `BACKUP_RETENTION_DAYS` | Limpieza backups | 🟢 No (default: 7) |

**Estado**: Todas las variables se configuran con `quickstart.sh` ✅

---

## ❌ PROBLEMAS ENCONTRADOS

### 1. **Directorios de Instancias Odoo NO se crean**

```bash
# FALTA en deploy.sh:
mkdir -p "$PROD_ROOT"  # /home/go/apps/production/odoo
mkdir -p "$DEV_ROOT"   # /home/go/apps/develop/odoo
```

**Impacto**: 🔴 CRÍTICO - El sistema fallará al intentar listar instancias

---

### 2. **Dependencias del Sistema NO se verifican completamente**

```bash
# FALTA verificar:
command -v psql >/dev/null 2>&1 || { echo "❌ psql no encontrado"; exit 1; }
command -v pg_dump >/dev/null 2>&1 || { echo "❌ pg_dump no encontrado"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git no encontrado"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "❌ jq no encontrado"; exit 1; }
command -v certbot >/dev/null 2>&1 || { echo "❌ certbot no encontrado"; exit 1; }
```

**Impacto**: 🟡 MEDIO - Funcionalidades fallarán silenciosamente

---

### 3. **Scripts de Odoo NO se hacen ejecutables**

```bash
# FALTA en deploy.sh:
chmod +x "$SCRIPTS_PATH/odoo/"*.sh
chmod +x "$SCRIPTS_PATH/utils/"*.sh
```

**Impacto**: 🔴 CRÍTICO - Scripts no se podrán ejecutar desde la API

---

### 4. **PostgreSQL NO se verifica que esté corriendo**

```bash
# FALTA en deploy.sh:
sudo systemctl status postgresql >/dev/null 2>&1 || {
    echo "❌ PostgreSQL no está corriendo"
    exit 1
}
```

**Impacto**: 🔴 CRÍTICO - Deploy fallará al crear la BD

---

### 5. **Usuario PostgreSQL NO se verifica que exista**

```bash
# FALTA en deploy.sh:
sudo -u postgres psql -c "\du" | grep -q "$DB_USER" || {
    echo "⚠️ Usuario PostgreSQL '$DB_USER' no existe"
    echo "Creando usuario..."
    sudo -u postgres createuser -s "$DB_USER"
}
```

**Impacto**: 🔴 CRÍTICO - No se podrá crear la BD

---

### 6. **Permisos sudo NO se verifican**

```bash
# FALTA en deploy.sh:
sudo -n true 2>/dev/null || {
    echo "❌ El usuario no tiene permisos sudo"
    exit 1
}
```

**Impacto**: 🟡 MEDIO - Deploy fallará en pasos que requieren sudo

---

## ✅ CONFIGURACIONES CORRECTAS

1. ✅ Backend Flask con límites de 1GB
2. ✅ Nginx con soporte para archivos grandes
3. ✅ Gunicorn con timeouts de 600s
4. ✅ Systemd con límites de recursos
5. ✅ Cron job para métricas
6. ✅ SSL con Let's Encrypt
7. ✅ DNS en Cloudflare
8. ✅ Directorios logs, data, backups
9. ✅ Archivos de datos (puertos, instancias)
10. ✅ Todas las dependencias Python

---

## 🔧 CAMBIOS NECESARIOS EN deploy.sh

### Prioridad CRÍTICA 🔴

```bash
# 1. Crear directorios de instancias Odoo
mkdir -p "$PROD_ROOT"
mkdir -p "$DEV_ROOT"

# 2. Hacer scripts ejecutables
chmod +x "$SCRIPTS_PATH/odoo/"*.sh
chmod +x "$SCRIPTS_PATH/utils/"*.sh

# 3. Verificar PostgreSQL
sudo systemctl status postgresql >/dev/null 2>&1 || {
    echo "❌ PostgreSQL no está corriendo"
    echo "Iniciando PostgreSQL..."
    sudo systemctl start postgresql
}

# 4. Verificar/crear usuario PostgreSQL
sudo -u postgres psql -c "\du" | grep -q "$DB_USER" || {
    echo "📦 Creando usuario PostgreSQL '$DB_USER'..."
    sudo -u postgres createuser -s "$DB_USER"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
}
```

### Prioridad MEDIA 🟡

```bash
# 5. Verificar dependencias adicionales
for cmd in psql pg_dump git jq certbot; do
    command -v $cmd >/dev/null 2>&1 || {
        echo "⚠️ $cmd no está instalado"
        MISSING_DEPS="$MISSING_DEPS $cmd"
    }
done

if [ -n "$MISSING_DEPS" ]; then
    echo "❌ Dependencias faltantes:$MISSING_DEPS"
    echo "Instalar con: sudo apt install postgresql-client git jq certbot python3-certbot-nginx"
    exit 1
fi

# 6. Verificar permisos sudo
sudo -n true 2>/dev/null || {
    echo "⚠️ Se requieren permisos sudo para continuar"
    echo "Ejecuta: sudo visudo"
    echo "Agrega: $USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/nginx"
}
```

---

## 📋 CHECKLIST DE VERIFICACIÓN POST-DEPLOY

### Base de Datos
- [ ] PostgreSQL está corriendo
- [ ] Usuario PostgreSQL existe
- [ ] Base de datos `server_panel` existe
- [ ] Tablas creadas (users, action_logs, github_configs, metrics_history)
- [ ] Usuario admin creado

### Directorios
- [ ] `/home/go/api-dev/logs` existe
- [ ] `/home/go/api-dev/data` existe
- [ ] `/home/go/backups` existe
- [ ] `/home/go/apps/production/odoo` existe
- [ ] `/home/go/apps/develop/odoo` existe

### Archivos
- [ ] `data/puertos_ocupados_odoo.txt` existe
- [ ] `data/dev-instances.txt` existe

### Scripts
- [ ] Scripts en `/scripts/odoo/` son ejecutables
- [ ] Scripts en `/scripts/utils/` son ejecutables

### Servicios
- [ ] `server-panel-api.service` está activo
- [ ] Nginx está corriendo
- [ ] SSL configurado correctamente
- [ ] Cron job de métricas configurado

### Red
- [ ] DNS en Cloudflare configurado
- [ ] Dominio resuelve a IP pública
- [ ] HTTPS funciona
- [ ] API responde en `/health`

### Dependencias
- [ ] python3.12 instalado
- [ ] node y npm instalados
- [ ] nginx instalado
- [ ] postgresql-client instalado
- [ ] git instalado
- [ ] jq instalado
- [ ] certbot instalado

---

## 🎯 RESUMEN EJECUTIVO

### Estado General: 🟡 BUENO CON MEJORAS NECESARIAS

**Configuraciones Correctas**: 10/16 (62.5%)  
**Problemas Críticos**: 4  
**Problemas Medios**: 2  

### Módulos Completamente Funcionales:
✅ Autenticación  
✅ Métricas  
✅ Logs  
✅ Backups (con configuraciones actualizadas)  
✅ GitHub Integration  
✅ Chunked Upload  

### Módulos con Problemas:
⚠️ Gestión de Instancias (directorios no se crean)  
⚠️ Scripts Odoo (no se hacen ejecutables)  

### Recomendación:
**Aplicar los cambios críticos antes de ejecutar deploy.sh en un entorno nuevo**

---

**Última actualización**: 2025-11-02  
**Próxima revisión**: Después de aplicar cambios
