# ⚡ Referencia Rápida - API-DEV

## 🚀 Comandos Esenciales

### Verificación del Sistema
```bash
# Verificación rápida
./check-system.sh

# Validación completa
source scripts/utils/validate-env.sh --full

# Ver configuración (sin credenciales)
grep -v "PASSWORD\|TOKEN\|SECRET" .env
```

### Gestión del Panel
```bash
# Desplegar panel
./deploy.sh

# Ver estado
sudo systemctl status server-panel-api

# Ver logs en tiempo real
sudo journalctl -u server-panel-api -f

# Reiniciar
sudo systemctl restart server-panel-api
```

### Instancias de Producción
```bash
# Crear instancia de producción
./scripts/odoo/init-production.sh production

# Eliminar instancia
./scripts/odoo/remove-production.sh

# Ver estado
sudo systemctl status odoo19e-*

# Ver logs
sudo journalctl -u odoo19e-NOMBRE -f
```

### Instancias de Desarrollo
```bash
# Crear instancia dev
./scripts/odoo/create-dev-instance.sh nombre-dev

# Eliminar instancia dev
./scripts/odoo/remove-dev-instance.sh

# Listar instancias
ls -la /home/go/apps/develop/odoo/
```

### Backups
```bash
# Hacer backup manual
./scripts/odoo/backup-production.sh

# Ver backups
ls -lh /home/go/backups/

# Configurar backup automático (cron)
crontab -e
# Agregar: 0 2 * * * /home/go/api-dev/scripts/odoo/backup-production.sh
```

## 🔧 Servicios

### PostgreSQL
```bash
# Estado
sudo systemctl status postgresql

# Iniciar/detener
sudo systemctl start postgresql
sudo systemctl stop postgresql

# Probar conexión
PGPASSWORD='tu_password' psql -h localhost -U go -d postgres

# Listar bases de datos
sudo -u postgres psql -l
```

### Nginx
```bash
# Estado
sudo systemctl status nginx

# Probar configuración
sudo nginx -t

# Reiniciar
sudo systemctl restart nginx

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

## 📁 Rutas Importantes

```bash
# Proyecto
/home/go/api-dev/

# Configuración
/home/go/api-dev/.env

# Scripts
/home/go/api-dev/scripts/odoo/
/home/go/api-dev/scripts/utils/

# Instancias Odoo
/home/go/apps/production/odoo/
/home/go/apps/develop/odoo/

# Backups
/home/go/backups/

# Logs
/var/log/nginx/
sudo journalctl -u server-panel-api
sudo journalctl -u odoo19e-*
```

## 🔍 Diagnóstico

### Ver Logs
```bash
# Panel API
sudo journalctl -u server-panel-api -n 100

# Nginx
sudo tail -f /var/log/nginx/error.log

# Instancia Odoo específica
sudo journalctl -u odoo19e-NOMBRE -n 100

# Todos los servicios Odoo
sudo journalctl -u "odoo19e-*" -n 50
```

### Ver Puertos
```bash
# Puertos en uso
sudo netstat -tlnp | grep LISTEN

# Puerto específico
sudo netstat -tlnp | grep :8069

# Ver archivo de puertos ocupados
cat /home/go/api-dev/data/puertos_ocupados_odoo.txt
```

### Ver Procesos
```bash
# Procesos Odoo
ps aux | grep odoo

# Procesos Python
ps aux | grep python

# Procesos Gunicorn
ps aux | grep gunicorn
```

## 🌐 DNS y Cloudflare

### Ver Registros DNS
```bash
# Obtener Zone ID
curl -X GET "https://api.cloudflare.com/client/v4/zones?name=tudominio.com" \
  -H "Authorization: Bearer TU_TOKEN" | jq

# Listar registros DNS
curl -X GET "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer TU_TOKEN" | jq
```

## 🔐 Seguridad

### Permisos del .env
```bash
# Verificar permisos (debe ser 600)
ls -la .env

# Corregir si es necesario
chmod 600 .env
```

### Backup del .env
```bash
# Crear backup
cp .env .env.backup.$(date +%Y%m%d)
chmod 600 .env.backup.*
```

## 📊 Monitoreo

### Espacio en Disco
```bash
# Ver uso general
df -h

# Ver uso por directorio
du -sh /home/go/apps/*
du -sh /home/go/backups/*
```

### Memoria
```bash
# Ver uso de memoria
free -h

# Ver procesos por memoria
ps aux --sort=-%mem | head -10
```

### CPU
```bash
# Ver carga del sistema
uptime

# Ver procesos por CPU
top
# o
htop
```

## 🔄 Actualización

### Actualizar desde Git
```bash
cd /home/go/api-dev
git pull origin main

# Reinstalar dependencias si es necesario
cd backend
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

### Reconstruir Frontend
```bash
cd /home/go/api-dev/frontend
npm run build
sudo systemctl restart nginx
```

## 🆘 Solución Rápida de Problemas

### Panel no carga
```bash
sudo systemctl restart server-panel-api
sudo systemctl restart nginx
sudo journalctl -u server-panel-api -n 50
```

### Instancia Odoo no inicia
```bash
# Ver logs
sudo journalctl -u odoo19e-NOMBRE -n 100

# Verificar puerto
netstat -tlnp | grep :PUERTO

# Reiniciar
sudo systemctl restart odoo19e-NOMBRE
```

### PostgreSQL no conecta
```bash
# Verificar servicio
sudo systemctl status postgresql

# Reiniciar
sudo systemctl restart postgresql

# Verificar credenciales en .env
grep DB_ .env
```

### Error de DNS
```bash
# Verificar registros
dig tudominio.com
dig api-dev.tudominio.com

# Verificar Cloudflare
curl -I https://api-dev.tudominio.com
```

## 📝 Variables de Entorno Clave

```bash
# Ver todas (sin credenciales)
grep -v "PASSWORD\|TOKEN\|SECRET" .env

# Variables críticas:
DOMAIN_ROOT=tudominio.com
API_DOMAIN=api-dev.tudominio.com
PUBLIC_IP=tu.ip.publica
PROD_INSTANCE_NAME=odoo-production
```

## 🎯 Flujo de Trabajo Típico

### Nuevo Servidor
```bash
1. git clone [repo] api-dev
2. cd api-dev
3. ./quickstart.sh
4. ./deploy.sh
5. ./scripts/odoo/init-production.sh production
```

### Nuevo Desarrollador
```bash
1. ./scripts/odoo/create-dev-instance.sh nombre-dev
2. Acceder a: https://nombre-dev.tudominio.com
3. Usuario: admin / Password: [configurado en .env]
```

### Backup y Restauración
```bash
# Backup
./scripts/odoo/backup-production.sh

# Ver backups
ls -lh /home/go/backups/

# Restaurar (manual)
# 1. Extraer backup
# 2. Restaurar BD: psql < database.sql
# 3. Restaurar filestore: tar -xzf filestore.tar.gz
```

## 📚 Documentación

```bash
# Ver documentación completa
ls -la docs/

# Archivos clave:
cat README.md                    # Visión general
cat NEXT_STEPS.md               # Próximos pasos
cat IMPLEMENTATION_SUMMARY.md   # Resumen completo
cat docs/MIGRATION_GUIDE.md     # Guía de migración
```

---

**Tip**: Guarda este archivo en marcadores para acceso rápido 🔖
