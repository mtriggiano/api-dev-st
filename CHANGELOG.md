# 📝 Changelog - API-DEV

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [2.3.0] - 2025-11-12

### ✨ Agregado (NUEVO)
- **Monitoreo de Commits en UI**
  - Badge con hash del commit actual debajo del botón GitHub
  - Tooltip con mensaje completo del commit
  - Actualización automática al cargar la página
  - Endpoint `GET /api/github/current-commit/<instance>`

- **Logs de Git/Deploy en Panel**
  - Nueva pestaña "Git/Deploy" en modal de logs
  - Historial completo de deploys automáticos y manuales
  - Formato: `[Fecha] ✅/❌ Acción: Detalles (Usuario)`
  - Endpoint `GET /api/github/deploy-logs/<instance>`
  - Incluye: webhooks, tests, git pull/push/commit

- **Soporte para Content-Type de GitHub**
  - Webhook acepta `application/json` y `application/x-www-form-urlencoded`
  - Respuesta automática a eventos `ping` de GitHub
  - Parsing correcto del payload según Content-Type

### 🔧 Corregido
- **DeployManager**: Rutas absolutas para comandos sudo y systemctl
  - Cambiado `sudo` → `/usr/bin/sudo`
  - Cambiado `systemctl` → `/usr/bin/systemctl`
  - Corregida ruta de producción: `/home/go/apps/production/odoo/`
  - Corregida ruta de odoo-bin: incluye `/odoo-server/`
  - Usuario correcto para ejecutar comandos: `go` (no `odoo`)

- **Frontend**: Botón de GitHub visible en todas las instancias
  - Removida restricción `!isProduction`
  - Agregada prop `onGitHub` a instancias de producción

### 📚 Documentación
- **GITHUB_INTEGRATION.md** - Actualizado con sección de Webhooks y Auto-Deploy
  - Guía completa de configuración de webhooks
  - Cómo monitorear commits y deploys
  - Endpoints de webhook documentados
  - Seguridad y validación explicada

- **GITHUB_IMPROVEMENTS.md** - Nuevo documento con mejoras implementadas
  - Resumen de funcionalidades
  - Guía de monitoreo de deploys
  - Comandos de debugging
  - Próximos pasos sugeridos

---

## [2.2.0] - 2025-11-12

### ✨ Agregado (MAYOR)
- **Sistema de Webhooks de GitHub para Auto-Deploy**
  - Webhook endpoint que recibe notificaciones de GitHub
  - Auto-deploy en push/merge a rama main (producción)
  - Validación de signature HMAC-SHA256
  - Actualización automática de módulos Odoo (opcional)
  - Reinicio automático de servicios
  
- **Detección Automática de Tipo de Instancia**
  - Desarrollo: Instancias que empiezan con `dev-` usan su nombre como rama
  - Producción: Instancias sin `dev-` usan rama `main`
  - Campo `instance_type` en modelo GitHubConfig
  
- **Nuevos Campos en GitHubConfig**
  - `instance_type`: 'development' o 'production'
  - `auto_deploy`: Habilitar/deshabilitar auto-deploy
  - `webhook_secret`: Secret para validar webhooks
  - `update_modules_on_deploy`: Actualizar módulos en deploy
  - `last_deploy_at`: Timestamp del último deploy

- **Nuevos Endpoints API**
  - `POST /api/github/webhook/config/<instance>` - Configurar webhook
  - `POST /api/github/webhook/<instance>` - Recibir webhook de GitHub
  - `POST /api/github/webhook/test/<instance>` - Probar webhook manualmente
  - `GET /api/github/current-commit/<instance>` - Obtener commit actual
  - `GET /api/github/deploy-logs/<instance>` - Obtener logs de deploy

- **DeployManager Service**
  - Servicio para gestionar deploys automáticos
  - Pull de cambios con autenticación
  - Actualización de módulos Odoo
  - Reinicio de servicios
  - Logging completo de operaciones

### 📚 Documentación
- **GITHUB_WEBHOOK.md** - Documentación completa del sistema de webhooks
  - Guía de configuración paso a paso
  - Ejemplos de uso
  - Troubleshooting detallado
  - Mejores prácticas de seguridad

### 🔄 Migración
- Script de migración `add_webhook_fields.py`
- Actualización automática de instancias existentes
- Detección de tipo basada en nombre de instancia

---

## [2.1.0] - 2025-11-12

### 🔧 Corregido (CRÍTICO)
- **Integración GitHub**: Solucionado error `[Errno 2] No such file or directory: 'git'`
  - El proceso de Gunicorn no heredaba el PATH completo del sistema
  - Ahora se usa la ruta absoluta `/usr/bin/git` en todos los comandos Git
  - Archivo modificado: `backend/services/git_manager.py` (línea 27-28)
  
### ✨ Agregado
- **Verificación de Git en quickstart.sh**
  - Verifica que Git esté instalado en `/usr/bin/git`
  - Muestra advertencia si está en otra ubicación
  - Sugiere crear symlink si es necesario

### 📚 Documentación
- **GITHUB_INTEGRATION.md actualizado**
  - Agregada sección de requisitos con verificación de Git
  - Nuevo troubleshooting para error de PATH de Git
  - Explicación técnica del problema y solución
  - Actualizada fecha de última modificación

### 🧪 Probado
- Circuito completo de integración GitHub verificado:
  - ✅ Verificación de token
  - ✅ Creación de configuración
  - ✅ Inicialización de repositorio
  - ✅ Detección de cambios
  - ✅ Commit, push, pull

---

## [2.0.0] - 2025-10-30

### ✨ Agregado
- **Refactorización completa del proyecto**
  - Configuración centralizada en archivo `.env`
  - Script `quickstart.sh` interactivo para configuración inicial
  - Estructura modular y organizada
  
- **Integración GitHub**
  - Control de versiones para custom addons
  - Endpoints para commit, push, pull
  - Gestión de tokens y configuraciones por instancia
  - Portal web para operaciones Git

- **Configuración SSL flexible**
  - Soporte para Let's Encrypt
  - Soporte para Cloudflare Origin Certificate
  - Opción de solo HTTP para desarrollo

- **Gestión de Backups**
  - Backup completo de producción (BD + archivos)
  - Restauración automatizada
  - Carga chunked para archivos grandes

### 🔧 Corregido
- Múltiples mejoras de seguridad
- Optimización de rendimiento
- Corrección de bugs menores

### 📚 Documentación
- Documentación completa en `/docs`
- Guías de instalación y configuración
- Ejemplos de uso de API
- Troubleshooting detallado

---

## [1.0.0] - 2025-09-15

### ✨ Versión Inicial
- Dashboard de métricas del servidor
- Gestión básica de instancias Odoo
- Logs centralizados
- Autenticación JWT
- Panel web con React

---

## Tipos de Cambios

- **✨ Agregado**: Para nuevas funcionalidades
- **🔧 Corregido**: Para correcciones de bugs
- **🔄 Cambiado**: Para cambios en funcionalidades existentes
- **🗑️ Eliminado**: Para funcionalidades eliminadas
- **🔒 Seguridad**: Para vulnerabilidades corregidas
- **📚 Documentación**: Para cambios en documentación
- **⚡ Rendimiento**: Para mejoras de rendimiento
- **🧪 Probado**: Para cambios en tests

---

## Notas de Migración

### De 2.0.x a 2.1.0

**Requisitos nuevos:**
- Git debe estar instalado en `/usr/bin/git`

**Pasos de actualización:**
```bash
# 1. Verificar Git
which git
ls -la /usr/bin/git

# 2. Si no está en /usr/bin/git, instalarlo o crear symlink
sudo apt install git -y
# O si ya está instalado en otra ubicación:
# sudo ln -s $(which git) /usr/bin/git

# 3. Actualizar código
cd /home/go/api-dev
git pull origin main

# 4. Reiniciar servicios
sudo systemctl restart server-panel-api
```

**Cambios incompatibles:**
- Ninguno. Esta versión es 100% compatible con 2.0.x

---

## Soporte

Para reportar bugs o solicitar funcionalidades:
- Email: mtg@grupoorange.ar
- GitHub Issues: [Crear issue](https://github.com/tu-repo/api-dev/issues)

---

**Mantenido por:** Miguel Triggiano  
**Última actualización:** 2025-11-12
