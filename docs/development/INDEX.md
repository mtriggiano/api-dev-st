# 📑 Índice de Documentación - API-DEV v2.0

## 🎯 Inicio Rápido

### Para Nuevos Usuarios:
1. **[README.md](README.md)** - Visión general del sistema
2. **[NEXT_STEPS.md](NEXT_STEPS.md)** - Guía paso a paso de próximos pasos
3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Comandos rápidos de referencia

### Para Ejecutar:
```bash
# 1. Configurar el sistema
./quickstart.sh

# 2. Verificar estado
./check-system.sh

# 3. Ver próximos pasos
cat NEXT_STEPS.md
```

---

## 📚 Documentación Principal

### Archivos en la Raíz:

| Archivo | Descripción | Cuándo Leer |
|---------|-------------|-------------|
| **[README.md](README.md)** | Visión general, características, estructura | Primero |
| **[NEXT_STEPS.md](NEXT_STEPS.md)** | Pasos detallados post-configuración | Después del quickstart |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | Comandos y referencias rápidas | Uso diario |
| **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** | Resumen completo de la refactorización | Para entender los cambios |
| **[POST_QUICKSTART_NOTES.md](POST_QUICKSTART_NOTES.md)** | Notas importantes después del quickstart | Después del quickstart |
| **[MIGRATION_STATE.md](MIGRATION_STATE.md)** | Estado del sistema antes de la migración | Referencia histórica |
| **[INDEX.md](INDEX.md)** | Este archivo - Índice de documentación | Navegación |

---

## 📁 Documentación en `/docs`

### Guías Detalladas:

| Archivo | Descripción | Cuándo Leer |
|---------|-------------|-------------|
| **[docs/QUICKSTART.md](docs/QUICKSTART.md)** | Guía de inicio rápido original | Referencia |
| **[docs/INSTALL.md](docs/INSTALL.md)** | Instalación manual paso a paso | Instalación manual |
| **[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** | Guía de migración desde versión anterior | Al migrar |
| **[docs/GITHUB_INTEGRATION.md](docs/GITHUB_INTEGRATION.md)** | Integración con GitHub | Para usar Git |
| **[docs/GITHUB_UI_TESTING.md](docs/GITHUB_UI_TESTING.md)** | Testing de UI de GitHub | Desarrollo |
| **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** | Solución de problemas | Cuando hay errores |
| **[docs/COMMANDS.md](docs/COMMANDS.md)** | Comandos disponibles | Referencia |
| **[docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** | Resumen del proyecto | Visión general |
| **[docs/STATUS.md](docs/STATUS.md)** | Estado del proyecto | Seguimiento |
| **[docs/README-DEV-INSTANCES.md](docs/README-DEV-INSTANCES.md)** | Gestión de instancias dev | Desarrollo |

---

## 🔧 Scripts Principales

### Scripts Ejecutables:

| Script | Descripción | Uso |
|--------|-------------|-----|
| **[quickstart.sh](quickstart.sh)** | Configuración interactiva inicial | `./quickstart.sh` |
| **[deploy.sh](deploy.sh)** | Despliegue del panel de control | `./deploy.sh` |
| **[check-system.sh](check-system.sh)** | Verificación rápida del sistema | `./check-system.sh` |

### Scripts de Odoo (`scripts/odoo/`):

| Script | Descripción | Uso |
|--------|-------------|-----|
| **[init-production.sh](scripts/odoo/init-production.sh)** | Crear instancia de producción | `./scripts/odoo/init-production.sh production` |
| **[remove-production.sh](scripts/odoo/remove-production.sh)** | Eliminar instancia de producción | `./scripts/odoo/remove-production.sh` |
| **[create-dev-instance.sh](scripts/odoo/create-dev-instance.sh)** | Crear instancia de desarrollo | `./scripts/odoo/create-dev-instance.sh nombre` |
| **[remove-dev-instance.sh](scripts/odoo/remove-dev-instance.sh)** | Eliminar instancia de desarrollo | `./scripts/odoo/remove-dev-instance.sh` |
| **[backup-production.sh](scripts/odoo/backup-production.sh)** | Backup de producción | `./scripts/odoo/backup-production.sh` |
| **[neutralize-database.py](scripts/odoo/neutralize-database.py)** | Neutralizar BD de desarrollo | Usado por create-dev-instance |

### Scripts de Utilidades (`scripts/utils/`):

| Script | Descripción | Uso |
|--------|-------------|-----|
| **[load-env.sh](scripts/utils/load-env.sh)** | Cargar variables de entorno | `source scripts/utils/load-env.sh` |
| **[validate-env.sh](scripts/utils/validate-env.sh)** | Validar configuración | `source scripts/utils/validate-env.sh --full` |

---

## 📋 Archivos de Configuración

### Configuración del Sistema:

| Archivo | Descripción | Editable |
|---------|-------------|----------|
| **[.env](.env)** | Variables de entorno (NO versionado) | ✅ Sí |
| **[.env.example](.env.example)** | Plantilla de variables | ❌ No (referencia) |
| **[.gitignore](.gitignore)** | Archivos ignorados por Git | ⚠️ Con cuidado |

### Configuración del Backend:

| Archivo | Descripción | Editable |
|---------|-------------|----------|
| **[backend/config.py](backend/config.py)** | Configuración de Flask | ⚠️ Con cuidado |
| **[backend/requirements.txt](backend/requirements.txt)** | Dependencias Python | ⚠️ Con cuidado |

### Configuración del Frontend:

| Archivo | Descripción | Editable |
|---------|-------------|----------|
| **[frontend/package.json](frontend/package.json)** | Dependencias Node | ⚠️ Con cuidado |
| **[frontend/vite.config.js](frontend/vite.config.js)** | Configuración Vite | ⚠️ Con cuidado |

---

## 🗂️ Archivos de Datos

### Datos del Sistema (`data/`):

| Archivo | Descripción | Propósito |
|---------|-------------|-----------|
| **[data/dev-instances.txt](data/dev-instances.txt)** | Registro de instancias dev | Tracking automático |
| **[data/puertos_ocupados_odoo.txt](data/puertos_ocupados_odoo.txt)** | Puertos en uso | Asignación automática |

---

## 🎓 Guías por Caso de Uso

### Caso 1: Primera Instalación
```
1. README.md (visión general)
2. ./quickstart.sh (ejecutar)
3. NEXT_STEPS.md (seguir pasos)
4. QUICK_REFERENCE.md (guardar para referencia)
```

### Caso 2: Migración desde Versión Anterior
```
1. IMPLEMENTATION_SUMMARY.md (entender cambios)
2. docs/MIGRATION_GUIDE.md (seguir guía)
3. ./quickstart.sh (reconfigurar)
4. NEXT_STEPS.md (continuar)
```

### Caso 3: Uso Diario
```
1. QUICK_REFERENCE.md (comandos rápidos)
2. ./check-system.sh (verificar estado)
3. docs/TROUBLESHOOTING.md (si hay problemas)
```

### Caso 4: Desarrollo
```
1. docs/README-DEV-INSTANCES.md (gestión de instancias)
2. docs/GITHUB_INTEGRATION.md (integración Git)
3. QUICK_REFERENCE.md (comandos útiles)
```

### Caso 5: Administración
```
1. QUICK_REFERENCE.md (comandos de gestión)
2. docs/COMMANDS.md (comandos avanzados)
3. docs/TROUBLESHOOTING.md (solución de problemas)
```

---

## 🔍 Búsqueda Rápida

### Buscar por Tema:

**Configuración:**
- `.env.example` - Plantilla de variables
- `POST_QUICKSTART_NOTES.md` - Notas de configuración
- `backend/config.py` - Configuración del backend

**Instalación:**
- `NEXT_STEPS.md` - Pasos de instalación
- `docs/INSTALL.md` - Instalación manual
- `docs/QUICKSTART.md` - Inicio rápido

**Gestión de Instancias:**
- `scripts/odoo/init-production.sh` - Crear producción
- `scripts/odoo/create-dev-instance.sh` - Crear desarrollo
- `docs/README-DEV-INSTANCES.md` - Guía de instancias

**Solución de Problemas:**
- `docs/TROUBLESHOOTING.md` - Guía de troubleshooting
- `QUICK_REFERENCE.md` - Comandos de diagnóstico
- `POST_QUICKSTART_NOTES.md` - Problemas comunes

**Comandos:**
- `QUICK_REFERENCE.md` - Referencia rápida
- `docs/COMMANDS.md` - Comandos detallados
- `check-system.sh` - Verificación automática

---

## 📊 Mapa de Navegación

```
API-DEV/
│
├── 📖 INICIO
│   ├── README.md ..................... Empieza aquí
│   ├── quickstart.sh ................. Configura el sistema
│   └── check-system.sh ............... Verifica estado
│
├── 📋 GUÍAS PRINCIPALES
│   ├── NEXT_STEPS.md ................. Próximos pasos
│   ├── QUICK_REFERENCE.md ............ Comandos rápidos
│   └── IMPLEMENTATION_SUMMARY.md ..... Resumen completo
│
├── 📁 DOCUMENTACIÓN DETALLADA (docs/)
│   ├── MIGRATION_GUIDE.md ............ Guía de migración
│   ├── INSTALL.md .................... Instalación manual
│   ├── TROUBLESHOOTING.md ............ Solución de problemas
│   └── [otros documentos]
│
├── 🔧 SCRIPTS
│   ├── scripts/odoo/ ................. Scripts de Odoo
│   └── scripts/utils/ ................ Utilidades
│
└── ⚙️ CONFIGURACIÓN
    ├── .env .......................... Variables (NO versionado)
    ├── .env.example .................. Plantilla
    └── backend/config.py ............. Config del backend
```

---

## 🆘 ¿Necesitas Ayuda?

### Según tu Situación:

| Situación | Lee Esto |
|-----------|----------|
| 🆕 Primera vez usando el sistema | `README.md` → `quickstart.sh` → `NEXT_STEPS.md` |
| 🔄 Migrando desde versión anterior | `IMPLEMENTATION_SUMMARY.md` → `docs/MIGRATION_GUIDE.md` |
| ⚠️ Tengo un error | `docs/TROUBLESHOOTING.md` → `QUICK_REFERENCE.md` |
| 📝 Necesito un comando específico | `QUICK_REFERENCE.md` |
| 🏭 Crear instancia de producción | `NEXT_STEPS.md` → `scripts/odoo/init-production.sh` |
| 👨‍💻 Crear instancia de desarrollo | `docs/README-DEV-INSTANCES.md` |
| 🔍 Verificar el sistema | `./check-system.sh` |
| 📚 Entender la refactorización | `IMPLEMENTATION_SUMMARY.md` |

---

## 📞 Soporte

### Recursos de Ayuda:

1. **Documentación**: Lee los archivos relevantes arriba
2. **Verificación**: Ejecuta `./check-system.sh`
3. **Logs**: `sudo journalctl -u server-panel-api -n 100`
4. **Validación**: `source scripts/utils/validate-env.sh --full`

---

**Última actualización**: $(date)  
**Versión**: 2.0.0 (Refactorizada)  
**Total de documentos**: 20+
