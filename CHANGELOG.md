# 📝 Changelog - API-DEV

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
