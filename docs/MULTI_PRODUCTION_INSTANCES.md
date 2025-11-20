# 🏭 Sistema de Múltiples Instancias de Producción

## 📋 Descripción General

API-DEV ahora soporta la creación de **múltiples instancias de producción de Odoo** en el mismo servidor, cada una con su propio subdominio.

### 🔒 Protección del Dominio Principal

**IMPORTANTE:** El sistema está diseñado para **NUNCA** modificar el dominio principal (`softrigx.com`). Todas las instancias de producción se crean automáticamente como subdominios.

## 🎯 Características Principales

- ✅ **Subdominios automáticos**: Cada instancia se crea como `[nombre].softrigx.com`
- ✅ **Protección del dominio raíz**: Validaciones múltiples impiden usar el dominio principal
- ✅ **SSL flexible**: Soporte para Cloudflare Origin, Let's Encrypt o HTTP
- ✅ **Gestión desde el panel**: Interfaz web para crear y gestionar instancias
- ✅ **Tracking automático**: Registro de todas las instancias creadas
- ✅ **Aislamiento completo**: Cada instancia tiene su propia BD, puerto y configuración

## 🚀 Uso desde el Panel Web

### Crear Nueva Instancia de Producción

1. **Acceder al panel**: Ir a la sección "Instancias"
2. **Clic en "Nueva Producción"** (botón verde)
3. **Ingresar nombre**: Solo letras minúsculas, números y guiones
   - ✅ Válido: `cliente1`, `empresa-abc`, `test-prod`
   - ❌ Inválido: `softrigx.com`, `production`, `MAYUSCULAS`
4. **Seleccionar método SSL**:
   - **Cloudflare Origin Certificate** (recomendado)
   - **Let's Encrypt** (certificado gratuito)
   - **HTTP** (sin SSL, solo para testing)
5. **Confirmar creación**
6. **Monitorear progreso**: El log se actualiza en tiempo real

### Ejemplo de Creación

```
Nombre ingresado: cliente1
Dominio resultante: cliente1.softrigx.com
Instancia interna: prod-cliente1
```

## 💻 Uso desde Línea de Comandos

### Crear Instancia

```bash
cd /home/mtg/api-dev
sudo ./scripts/odoo/create-prod-instance.sh cliente1
```

El script te preguntará:
1. Método SSL (1=Cloudflare, 2=Let's Encrypt, 3=HTTP)
2. Confirmará el dominio que se creará

### Verificar Instancias Creadas

```bash
# Ver lista de instancias de producción
cat /home/mtg/api-dev/data/prod-instances.txt

# Ver puertos ocupados
cat /home/mtg/api-dev/data/puertos_ocupados_odoo.txt

# Listar carpetas de instancias
ls -la /home/mtg/apps/production/odoo/
```

### Gestionar Instancia

```bash
# Ver estado
sudo systemctl status odoo19e-prod-cliente1

# Reiniciar
sudo systemctl restart odoo19e-prod-cliente1

# Ver logs
sudo journalctl -u odoo19e-prod-cliente1 -n 50 --no-pager

# Ver información completa
cat /home/mtg/apps/production/odoo/prod-cliente1/info-instancia.txt
```

## 🔐 Validaciones de Seguridad

El sistema tiene **múltiples capas de validación** para proteger el dominio principal:

### 1. Validación en el Script Bash
```bash
# Nombres prohibidos
if [[ "$INSTANCE" == "$CF_ZONE_NAME" ]] || 
   [[ "$INSTANCE" == "production" ]] || 
   [[ "$INSTANCE" == "prod" ]]; then
    echo "❌ ERROR: Nombre reservado"
    exit 1
fi
```

### 2. Validación en el Backend Python
```python
forbidden_names = [domain_root, 'production', 'prod', 'www', 'api', 'mail', 'ftp']
if name.lower() in forbidden_names:
    return {'error': 'Nombre prohibido'}
```

### 3. Validación de Formato DNS
```python
if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', name.lower()):
    return {'error': 'Formato inválido'}
```

### 4. Validación en el Frontend
```javascript
// Sanitización automática del input
onChange={(e) => setNewProdInstanceName(
  e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '')
)}
```

## 📁 Estructura de Archivos

### Ubicación de Instancias
```
/home/mtg/apps/production/odoo/
├── prod-cliente1/
│   ├── odoo-server/
│   ├── custom_addons/
│   ├── venv/
│   ├── odoo.conf
│   ├── odoo.log
│   └── info-instancia.txt
├── prod-cliente2/
└── prod-empresa-abc/
```

### Archivos de Tracking
```
/home/mtg/api-dev/data/
├── prod-instances.txt      # Lista de instancias de producción
├── dev-instances.txt       # Lista de instancias de desarrollo
└── puertos_ocupados_odoo.txt  # Puertos en uso
```

### Logs de Creación
```
/tmp/
└── odoo-create-prod-[nombre].log  # Log completo de creación
```

## 🌐 Configuración DNS y SSL

### DNS en Cloudflare
Cada instancia crea automáticamente:
- **Tipo**: A Record
- **Nombre**: `[nombre].softrigx.com`
- **Contenido**: IP pública del servidor
- **Proxy**: Activado (naranja)
- **TTL**: 3600 segundos

### Nginx
Cada instancia tiene su propia configuración:
```
/etc/nginx/sites-available/prod-[nombre]
/etc/nginx/sites-enabled/prod-[nombre]
```

### Systemd
Cada instancia tiene su propio servicio:
```
/etc/systemd/system/odoo19e-prod-[nombre].service
```

## 🔧 Configuración Técnica

### Puertos
- **HTTP**: Asignado automáticamente (rango 2100-3000)
- **Evented/Gevent**: Asignado automáticamente (rango 8072-8999)

### Base de Datos
- **Nombre**: `prod-[nombre]`
- **Usuario**: Configurado en `.env` (DB_USER)
- **Encoding**: UTF8

### Python
- **Versión**: 3.12 (configurable en `.env`)
- **Entorno virtual**: Aislado por instancia
- **Módulos base**: base, web, web_enterprise, contacts, l10n_ar

## 📊 Monitoreo

### Desde el Panel Web
- Estado del servicio (activo/inactivo)
- Dominio y puerto
- Logs en tiempo real
- Reinicio de servicio

### Desde Línea de Comandos
```bash
# Estado de todos los servicios Odoo
systemctl list-units | grep odoo19e

# Recursos del sistema
htop

# Conexiones de red
ss -tulpn | grep odoo
```

## ⚠️ Consideraciones Importantes

### Recursos del Servidor
Cada instancia de producción consume:
- **RAM**: ~500MB - 1GB (con 2 workers)
- **CPU**: Variable según carga
- **Disco**: ~2GB inicial + datos

### Límites Recomendados
- **Servidor pequeño** (4GB RAM): 2-3 instancias de producción
- **Servidor mediano** (8GB RAM): 4-6 instancias de producción
- **Servidor grande** (16GB+ RAM): 8+ instancias de producción

### Backup
Cada instancia debe tener su propio plan de backup:
```bash
# Backup manual de una instancia
pg_dump prod-cliente1 > /home/mtg/backups/prod-cliente1-$(date +%Y%m%d).sql
tar -czf /home/mtg/backups/prod-cliente1-files-$(date +%Y%m%d).tar.gz \
  /home/mtg/apps/production/odoo/prod-cliente1
```

## 🐛 Solución de Problemas

### La instancia no se crea
1. Verificar log: `cat /tmp/odoo-create-prod-[nombre].log`
2. Verificar permisos: `ls -la /home/mtg/apps/production/odoo/`
3. Verificar espacio: `df -h`

### El servicio no inicia
```bash
# Ver error específico
sudo journalctl -u odoo19e-prod-[nombre] -n 50

# Verificar configuración
cat /home/mtg/apps/production/odoo/prod-[nombre]/odoo.conf

# Verificar puerto
lsof -i :[puerto]
```

### DNS no resuelve
```bash
# Verificar en Cloudflare
dig [nombre].softrigx.com @1.1.1.1

# Verificar registro A
nslookup [nombre].softrigx.com
```

### SSL no funciona
```bash
# Verificar certificado
openssl s_client -connect [nombre].softrigx.com:443

# Verificar configuración Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## 📝 Ejemplos de Uso

### Caso 1: Cliente Nuevo
```bash
# Crear instancia para cliente "acme"
./scripts/odoo/create-prod-instance.sh acme

# Resultado:
# - Dominio: acme.softrigx.com
# - Instancia: prod-acme
# - BD: prod-acme
```

### Caso 2: Ambiente de Testing
```bash
# Crear instancia de testing
./scripts/odoo/create-prod-instance.sh testing

# Resultado:
# - Dominio: testing.softrigx.com
# - Instancia: prod-testing
# - BD: prod-testing
```

### Caso 3: Múltiples Sucursales
```bash
# Sucursal Norte
./scripts/odoo/create-prod-instance.sh sucursal-norte

# Sucursal Sur
./scripts/odoo/create-prod-instance.sh sucursal-sur

# Resultado:
# - sucursal-norte.softrigx.com
# - sucursal-sur.softrigx.com
```

## 🔄 Actualización del Sistema

Para actualizar el sistema API-DEV con los nuevos cambios:

```bash
cd /home/mtg/api-dev
./update.sh
```

Esto actualizará:
- Scripts de creación
- Backend (API)
- Frontend (Panel web)
- Configuraciones

## 📚 Referencias

- **Script principal**: `/home/mtg/api-dev/scripts/odoo/create-prod-instance.sh`
- **Backend**: `/home/mtg/api-dev/backend/services/instance_manager.py`
- **API Routes**: `/home/mtg/api-dev/backend/routes/instances.py`
- **Frontend**: `/home/mtg/api-dev/frontend/src/components/Instances.jsx`
- **Configuración**: `/home/mtg/api-dev/.env`

## 🆘 Soporte

Para problemas o dudas:
1. Revisar logs: `/tmp/odoo-create-prod-*.log`
2. Verificar documentación: Este archivo
3. Revisar configuración: `.env` y `info-instancia.txt`

---

**Versión**: 1.0  
**Fecha**: Noviembre 2024  
**Autor**: API-DEV System
