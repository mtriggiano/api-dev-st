# 🖥️ API-DEV - Sistema de Gestión de Instancias Odoo

**Sistema profesional para gestionar instancias Odoo y monitorear el servidor Ubuntu**

⚠️ **IMPORTANTE**: Este proyecto ha sido refactorizado para facilitar el despliegue en nuevos entornos. Todas las configuraciones sensibles ahora se manejan mediante variables de entorno.

---

## 🆕 Versión 2.0 - Refactorizada

✅ **Configuración centralizada** - Todo en archivo `.env`  
✅ **Despliegue automatizado** - Script `quickstart.sh` interactivo  
✅ **Seguridad mejorada** - Sin credenciales hardcodeadas  
✅ **Estructura organizada** - Proyecto completamente modular  
✅ **Documentación completa** - Guías paso a paso  

### 📊 Estado del Sistema
```bash
# Verificación rápida
./check-system.sh
```

## 🎆 Inicio Rápido

### Configuración Inicial (Primera vez)

```bash
# 1. Ejecutar el script de configuración interactivo
./quickstart.sh

# 2. Verificar la configuración
source scripts/utils/validate-env.sh --full

# 3. Desplegar el panel de control
./deploy.sh
```

### Acceso

- **URL**: Configurada durante el quickstart (ej: https://api-dev.tudominio.com)
- **Usuario por defecto**: admin
- **Contraseña por defecto**: admin123 (cambiar después del primer login)

## 🚀 Características

### Dashboard de Métricas
- **CPU**: Uso en tiempo real, cores, frecuencia
- **RAM**: Memoria usada/total, porcentaje, swap
- **Disco**: Uso por partición, espacio disponible
- **Red**: Tráfico entrante/saliente, velocidad
- **Uptime**: Tiempo de actividad del servidor
- **Gráficos históricos**: Últimos 60 minutos

### Gestión de Instancias Odoo
- **Listar instancias**: Producción y desarrollo
- **Crear instancias dev**: Clonadas desde producción
- **Actualizar BD**: Sincronizar con producción
- **Actualizar archivos**: Sincronizar código
- **Reiniciar instancias**: Control de servicios
- **Eliminar instancias**: Limpieza completa
- **Ver logs en tiempo real**: Por instancia

### Logs Centralizados
- **Historial de acciones**: Todas las operaciones
- **Filtros**: Por instancia, acción, período
- **Estadísticas**: Éxito/errores, gráficos
- **Auditoría**: Usuario, timestamp, detalles

### Autenticación y Seguridad
- **Login con JWT**: Tokens seguros
- **Roles**: Admin, Developer, Viewer
- **Sesiones**: Control de acceso
- **Logs de auditoría**: Todas las acciones

### Gestión de Backups y Restauración 💾
- **Backup de producción**: Crear backups completos (BD + archivos)
- **Subir backups**: Carga chunked para archivos grandes (hasta 1GB)
- **Listar backups**: Ver todos los backups disponibles con detalles
- **Restaurar producción**: Restaurar BD y archivos desde backup
- **Gestión automática**: Scripts de backup y restauración
- **Progreso en tiempo real**: Seguimiento de carga y restauración

### Configuración SSL Flexible 🔐 (Nuevo)
- **Múltiples opciones**: Let's Encrypt, Cloudflare Origin, o solo HTTP
- **Selección interactiva**: Elige el método al crear instancias
- **Sin límites de tasa**: Usa Cloudflare para evitar límites de Let's Encrypt
- **Certificados de 15 años**: Con Cloudflare Origin Certificate
- **Renovación automática**: Let's Encrypt se renueva cada 90 días
- **Configuración simplificada**: Todo automatizado

👉 **Ver documentación completa:** [SSL_CONFIGURATION.md](docs/SSL_CONFIGURATION.md)

### Integración GitHub 🔗
- **Control de versiones**: Git para custom addons
- **Vincular cuenta GitHub**: Conectar repositorios personales
- **Operaciones Git**: Commit, push, pull desde el panel
- **Historial**: Ver commits y cambios
- **Diff**: Visualizar diferencias en archivos
- **Gestión por instancia**: Cada desarrollador su repo

👉 **Ver documentación completa:** [GITHUB_INTEGRATION.md](GITHUB_INTEGRATION.md)

## 📁 Estructura del Proyecto (Refactorizada)

```
/home/go/api-dev/
├── .env                        # ⭐ Variables de entorno (NO versionado)
├── .env.example                # Plantilla para nuevos entornos
├── .gitignore                  # Protección de credenciales
├── quickstart.sh               # ⭐ Script interactivo de configuración
├── deploy.sh                   # Script de despliegue
├── README.md                   # Este archivo
│
├── backend/                    # Flask API
│   ├── app.py                 # Aplicación principal
│   ├── config.py              # Configuración (usa .env)
│   ├── models.py              # Modelos de BD
│   ├── wsgi.py                # Entry point para Gunicorn
│   ├── routes/                # Endpoints API
│   ├── services/              # Lógica de negocio
│   └── requirements.txt       # Dependencias Python
│
├── frontend/                   # React + Vite
│   ├── src/                   # Código fuente
│   ├── package.json           # Dependencias Node
│   └── vite.config.js         # Configuración Vite
│
├── scripts/                    # ⭐ Scripts de gestión
│   ├── odoo/                  # Scripts de Odoo
│   │   ├── init-production.sh       # Crear instancia producción
│   │   ├── remove-production.sh     # Eliminar instancia producción
│   │   ├── create-dev-instance.sh   # Crear instancia desarrollo
│   │   ├── remove-dev-instance.sh   # Eliminar instancia desarrollo
│   │   ├── backup-production.sh     # Backup de producción
│   │   └── neutralize-database.py   # Neutralizar BD desarrollo
│   └── utils/                 # Utilidades
│       ├── load-env.sh        # Cargar variables de entorno
│       └── validate-env.sh    # Validar configuración
│
├── data/                       # ⭐ Datos del sistema
│   ├── dev-instances.txt      # Registro de instancias dev
│   └── puertos_ocupados_odoo.txt # Puertos en uso
│
├── docs/                       # Documentación
│   ├── QUICKSTART.md          # Guía de inicio rápido
│   ├── INSTALL.md             # Instalación manual
│   ├── SSL_CONFIGURATION.md   # ⭐ Configuración SSL (Nuevo)
│   ├── TROUBLESHOOTING.md     # Solución de problemas
│   ├── GITHUB_INTEGRATION.md  # Integración con GitHub
│   └── [otros documentos]
│
└── config/                     # Templates de configuración
    └── [templates futuros]
```

## 🛠️ Instalación y Despliegue

### Requisitos Previos

- Ubuntu Server
- Python 3.12
- Node.js 20+
- PostgreSQL
- Nginx
- Certbot

### Despliegue Automático (Nuevo Método)

```bash
# Primera vez - Configuración inicial
cd /home/go/api-dev
./quickstart.sh

# Desplegar el sistema
./deploy.sh
```

El script automáticamente:
1. Configura DNS en Cloudflare
2. Instala dependencias
3. Crea base de datos PostgreSQL
4. Configura backend con Gunicorn
5. Construye frontend
6. Configura Nginx con SSL
7. Crea servicio systemd
8. Configura cron para métricas

### Gestión de Instancias Odoo

```bash
# Crear instancia de producción
./scripts/odoo/init-production.sh production

# Crear instancia de desarrollo
./scripts/odoo/create-dev-instance.sh nombre-desarrollador

# Hacer backup de producción
./scripts/odoo/backup-production.sh
```

## 🔧 Configuración

### Variables de Entorno

Todas las configuraciones se manejan desde el archivo `.env` en la raíz del proyecto.

**⚠️ IMPORTANTE**: 
- El archivo `.env` se genera automáticamente con `./quickstart.sh`
- NUNCA versiones el archivo `.env` en Git
- Usa `.env.example` como referencia para nuevos entornos
- Mantén permisos seguros: `chmod 600 .env`

Variables principales:
- `DOMAIN_ROOT`: Tu dominio principal
- `CF_API_TOKEN`: Token de Cloudflare
- `DB_PASSWORD`: Contraseña de PostgreSQL
- `ODOO_ADMIN_PASSWORD`: Contraseña admin de Odoo
- `PROD_INSTANCE_NAME`: Nombre de instancia producción (default: odoo-production)

Ver `.env.example` para la lista completa de variables.

## 📊 API Endpoints

### Autenticación
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Usuario actual
- `POST /api/auth/refresh` - Refrescar token

### Métricas
- `GET /api/metrics/current` - Métricas actuales
- `GET /api/metrics/history?minutes=60` - Historial

### Instancias
- `GET /api/instances` - Listar instancias
- `GET /api/instances/:name` - Detalle de instancia
- `POST /api/instances/create` - Crear instancia dev
- `DELETE /api/instances/:name` - Eliminar instancia
- `POST /api/instances/:name/update-db` - Actualizar BD
- `POST /api/instances/:name/update-files` - Actualizar archivos
- `POST /api/instances/:name/restart` - Reiniciar instancia
- `GET /api/instances/:name/logs?lines=100` - Ver logs

### Logs
- `GET /api/logs?instance=&action=&hours=24` - Listar logs
- `GET /api/logs/stats?hours=24` - Estadísticas

### Backups (Nuevo)
- `GET /api/backup/list` - Listar todos los backups disponibles
- `POST /api/backup/create` - Crear backup de producción
- `POST /api/backup/upload` - Subir archivo de backup (chunked)
- `POST /api/backup/restore` - Restaurar producción desde backup
- `GET /api/backup/status/:task_id` - Estado de tarea de backup/restore

### GitHub
- `POST /api/github/verify-token` - Verificar token de GitHub
- `GET /api/github/repos` - Listar repositorios del usuario
- `GET /api/github/config` - Listar configuraciones
- `GET /api/github/config/:instance` - Obtener configuración
- `POST /api/github/config` - Crear/actualizar configuración
- `DELETE /api/github/config/:instance` - Eliminar configuración
- `POST /api/github/init-repo` - Inicializar repositorio Git
- `GET /api/github/status/:instance` - Estado del repositorio
- `POST /api/github/commit` - Crear commit
- `POST /api/github/push` - Push al remoto
- `POST /api/github/pull` - Pull del remoto
- `GET /api/github/history/:instance` - Historial de commits
- `GET /api/github/diff/:instance` - Diff de cambios

## 🔐 Roles y Permisos

### Admin
- ✅ Ver dashboard y métricas
- ✅ Ver instancias
- ✅ Crear instancias dev
- ✅ Actualizar instancias (BD y archivos)
- ✅ Reiniciar instancias
- ✅ Eliminar instancias
- ✅ Ver logs
- ✅ Gestión de Backups (crear, subir, restaurar)
- ✅ Gestión GitHub (vincular, commit, push, pull)

### Developer
- ✅ Ver dashboard y métricas
- ✅ Ver instancias
- ✅ Crear instancias dev
- ✅ Actualizar instancias (BD y archivos)
- ✅ Reiniciar instancias
- ❌ Eliminar instancias
- ✅ Ver logs
- ✅ Ver backups (solo listar)
- ✅ Gestión GitHub (vincular, commit, push, pull)

### Viewer
- ✅ Ver dashboard y métricas
- ✅ Ver instancias
- ❌ Crear instancias
- ❌ Actualizar instancias
- ❌ Reiniciar instancias
- ❌ Eliminar instancias
- ✅ Ver logs
- ✅ Ver backups (solo listar)
- ❌ Gestión GitHub

## 🛠️ Comandos Útiles

### Backend

```bash
# Ver logs
sudo journalctl -u server-panel-api -f

# Reiniciar servicio
sudo systemctl restart server-panel-api

# Estado del servicio
sudo systemctl status server-panel-api

# Detener servicio
sudo systemctl stop server-panel-api
```

### Frontend

```bash
# Desarrollo local
cd /home/go/api/frontend
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

### Base de Datos

```bash
# Conectar a PostgreSQL
sudo -u postgres psql -d server_panel

# Ver tablas
\dt

# Ver usuarios
SELECT * FROM users;

# Ver logs recientes
SELECT * FROM action_logs ORDER BY timestamp DESC LIMIT 10;
```

### Nginx

```bash
# Verificar configuración
sudo nginx -t

# Recargar configuración
sudo systemctl reload nginx

# Ver logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 🔄 Actualización

Para actualizar el panel después de cambios en el código:

```bash
cd /home/go/api

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart server-panel-api

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

## 🐛 Solución de Problemas

### El backend no inicia

```bash
# Ver logs detallados
sudo journalctl -u server-panel-api -n 100 --no-pager

# Verificar que el puerto 5000 esté libre
sudo netstat -tlnp | grep 5000

# Verificar variables de entorno
cat /home/go/api/backend/.env
```

### Error de conexión a la base de datos

```bash
# Verificar que la BD existe
sudo -u postgres psql -l | grep server_panel

# Verificar permisos
sudo -u postgres psql -c "\du"

# Recrear BD
sudo -u postgres dropdb server_panel
sudo -u postgres createdb server_panel -O go --encoding='UTF8'
cd /home/go/api/backend
source venv/bin/activate
python3 -c "from app import create_app, init_db; app = create_app(); init_db(app)"
```

### Error 502 en Nginx

```bash
# Verificar que el backend esté corriendo
sudo systemctl status server-panel-api

# Verificar configuración de Nginx
sudo nginx -t

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### Las métricas no se guardan

```bash
# Verificar cron job
crontab -l | grep metrics

# Probar manualmente
curl -X POST http://localhost:5000/api/metrics/save

# Ver logs del cron
grep CRON /var/log/syslog
```

## 📝 Notas Importantes

1. **Cambiar contraseña por defecto**: Después del primer login, cambiar la contraseña del usuario admin
2. **Backup de BD**: Hacer backups regulares de la base de datos `server_panel`
3. **Backups de Odoo**: Los backups se almacenan en `/home/go/backups` y pueden ocupar mucho espacio. Considerar limpieza periódica
4. **Carga de archivos**: El sistema soporta archivos hasta 1GB usando carga chunked
5. **Logs**: Los logs de acciones se guardan en la BD y pueden crecer. Considerar limpieza periódica
6. **Métricas**: Se guardan cada minuto. Considerar limpieza de métricas antiguas
7. **Permisos sudo**: El usuario `go` necesita permisos sudo para gestionar servicios systemd
8. **GitHub Tokens**: Los tokens de acceso se almacenan en BD. En producción, considerar encriptación
9. **Integración GitHub**: Ver [GITHUB_INTEGRATION.md](GITHUB_INTEGRATION.md) para guía completa

## 🆘 Soporte

Para problemas o dudas:
1. Revisar logs del backend: `sudo journalctl -u server-panel-api -f`
2. Revisar logs de Nginx: `sudo tail -f /var/log/nginx/error.log`
3. Verificar estado de servicios: `sudo systemctl status server-panel-api`
4. Revisar este README

---

**Última actualización**: 2025-10-30
