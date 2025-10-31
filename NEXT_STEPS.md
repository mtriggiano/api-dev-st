# 🎯 Próximos Pasos - Sistema API-DEV

## ✅ Estado Actual

### Completado:
- ✅ Refactorización completa del sistema
- ✅ Configuración inicial con quickstart
- ✅ Archivo `.env` generado
- ✅ Estructura de directorios creada
- ✅ Scripts refactorizados y funcionales
- ✅ Validación de variables exitosa
- ✅ Conexión con Cloudflare verificada

### Pendiente:
- ⚠️ Conexión con PostgreSQL (requiere verificación)
- ⏳ Despliegue del panel de control
- ⏳ Creación de instancia de producción

---

## 🔧 Paso 1: Verificar y Corregir PostgreSQL

### Verificar el servicio:
```bash
sudo systemctl status postgresql
```

### Si no está activo, iniciarlo:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Verificar la contraseña del usuario:
```bash
# Conectar como postgres
sudo -u postgres psql

# Dentro de psql, verificar/cambiar contraseña
postgres=# \du
postgres=# ALTER USER go WITH PASSWORD 'Phax0r!261400*';
postgres=# \q
```

### Probar la conexión:
```bash
# Usar la contraseña configurada en .env
PGPASSWORD='Phax0r!261400*' psql -h localhost -U go -d postgres -c '\l'
```

### Si la conexión falla, verificar pg_hba.conf:
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Debe contener (agregar si no existe):
# local   all             go                                      md5
# host    all             go              127.0.0.1/32            md5

# Reiniciar PostgreSQL después de cambios
sudo systemctl restart postgresql
```

---

## 🚀 Paso 2: Desplegar el Panel de Control

Una vez que PostgreSQL esté funcionando:

```bash
cd /home/go/api-dev
./deploy.sh
```

### El script deploy.sh hará:
1. ✅ Configurar DNS en Cloudflare
2. ✅ Crear base de datos `server_panel`
3. ✅ Instalar dependencias del backend
4. ✅ Configurar servicio systemd
5. ✅ Construir frontend
6. ✅ Configurar Nginx con SSL
7. ✅ Obtener certificado Let's Encrypt

### Acceder al panel:
```
URL: https://api-dev.grupoorange.ar
Usuario: admin
Contraseña: admin123
```

**⚠️ IMPORTANTE**: Cambiar la contraseña después del primer login.

---

## 🏭 Paso 3: Crear Instancia de Producción Odoo

### Opción A: Usar el nombre configurado en .env

El quickstart configuró `PROD_INSTANCE_NAME=go`, pero se recomienda cambiarlo:

```bash
# Editar .env
nano /home/go/api-dev/.env

# Cambiar:
# PROD_INSTANCE_NAME=go
# Por:
# PROD_INSTANCE_NAME=odoo-production
```

### Opción B: Crear con el nombre actual

```bash
# Crear instancia con el nombre "go"
./scripts/odoo/init-production.sh production

# Esto creará:
# - Instancia: /home/go/apps/production/odoo/go/
# - Base de datos: go
# - Dominio: grupoorange.ar (dominio raíz)
```

### Opción C: Crear con nombre personalizado

```bash
# Especificar un nombre diferente
./scripts/odoo/init-production.sh mi-empresa

# Esto creará:
# - Instancia: /home/go/apps/production/odoo/mi-empresa/
# - Base de datos: mi-empresa
# - Dominio: mi-empresa.grupoorange.ar
```

---

## 👨‍💻 Paso 4: Crear Instancias de Desarrollo

```bash
# Crear instancia de desarrollo para un programador
./scripts/odoo/create-dev-instance.sh nombre-dev

# Ejemplo:
./scripts/odoo/create-dev-instance.sh martin
./scripts/odoo/create-dev-instance.sh juan
```

### Cada instancia de desarrollo:
- Clona la base de datos de producción
- Copia el filestore
- Neutraliza la BD (elimina licencia, desactiva correos/crons)
- Crea dominio: `nombre-dev.grupoorange.ar`
- Asigna puerto automáticamente

---

## 💾 Paso 5: Configurar Backups Automáticos

### Crear cron job para backups diarios:

```bash
# Editar crontab
crontab -e

# Agregar (backup diario a las 2 AM):
0 2 * * * /home/go/api-dev/scripts/odoo/backup-production.sh >> /var/log/odoo-backup.log 2>&1
```

### Probar backup manualmente:
```bash
./scripts/odoo/backup-production.sh
```

### Verificar backups:
```bash
ls -lh /home/go/backups/
```

---

## 🔍 Verificación Final

### Checklist de verificación:

```bash
# 1. Verificar variables de entorno
cd /home/go/api-dev
source scripts/utils/validate-env.sh --full

# 2. Verificar servicios
sudo systemctl status postgresql
sudo systemctl status nginx
sudo systemctl status server-panel-api

# 3. Verificar instancias Odoo (después de crearlas)
sudo systemctl status odoo19e-*

# 4. Verificar logs
sudo journalctl -u server-panel-api -n 50
sudo journalctl -u odoo19e-* -n 50

# 5. Verificar conectividad
curl -I https://api-dev.grupoorange.ar
curl -I https://grupoorange.ar  # Después de crear producción
```

---

## 📊 Comandos Útiles

### Ver configuración actual:
```bash
# Ver variables (sin mostrar credenciales)
grep -v "PASSWORD\|TOKEN\|SECRET" /home/go/api-dev/.env

# Ver instancias de producción
ls -la /home/go/apps/production/odoo/

# Ver instancias de desarrollo
ls -la /home/go/apps/develop/odoo/

# Ver backups
ls -lh /home/go/backups/
```

### Gestión de instancias:
```bash
# Listar servicios Odoo
sudo systemctl list-units "odoo19e-*"

# Ver logs de una instancia
sudo journalctl -u odoo19e-nombre-instancia -f

# Reiniciar una instancia
sudo systemctl restart odoo19e-nombre-instancia

# Eliminar instancia de desarrollo
./scripts/odoo/remove-dev-instance.sh nombre-dev
```

### Gestión del panel:
```bash
# Ver logs del panel
sudo journalctl -u server-panel-api -f

# Reiniciar el panel
sudo systemctl restart server-panel-api

# Ver estado de Nginx
sudo nginx -t
sudo systemctl status nginx
```

---

## 🐛 Solución de Problemas

### El panel no carga:
```bash
# Verificar servicio
sudo systemctl status server-panel-api

# Ver logs
sudo journalctl -u server-panel-api -n 100

# Verificar Nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Instancia Odoo no inicia:
```bash
# Ver logs
sudo journalctl -u odoo19e-nombre -n 100

# Verificar puerto
netstat -tlnp | grep :8069

# Verificar base de datos
sudo -u postgres psql -l | grep nombre-instancia
```

### Error de DNS:
```bash
# Verificar registros en Cloudflare
curl -X GET "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer $(grep CF_API_TOKEN .env | cut -d'=' -f2)" \
  -H "Content-Type: application/json" | jq
```

---

## 📚 Documentación Adicional

- **Guía de Migración**: `docs/MIGRATION_GUIDE.md`
- **Instalación Manual**: `docs/INSTALL.md`
- **Integración GitHub**: `docs/GITHUB_INTEGRATION.md`
- **README Principal**: `README.md`

---

## 🎉 Resumen

### Configuración Actual:
- **Dominio**: grupoorange.ar
- **Panel**: api-dev.grupoorange.ar
- **IP**: 200.69.140.3
- **Usuario**: go
- **Instancia Prod**: go (recomendado cambiar a `odoo-production`)

### Para Empezar:
1. Corregir PostgreSQL (si es necesario)
2. Ejecutar `./deploy.sh`
3. Crear instancia de producción
4. Acceder al panel y gestionar desde ahí

### Soporte:
- Logs del sistema: `sudo journalctl -xe`
- Logs del panel: `sudo journalctl -u server-panel-api`
- Validación: `source scripts/utils/validate-env.sh --full`

---

**¡El sistema está listo para ser desplegado!** 🚀
