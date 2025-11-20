# 📝 Notas Post-Quickstart

## ✅ Configuración Completada

El quickstart se ejecutó exitosamente con la siguiente configuración:

### Configuración Aplicada:
- **Dominio**: `grupoorange.ar`
- **Panel**: `https://api-dev.grupoorange.ar`
- **IP Pública**: `200.69.140.3`
- **Usuario**: `go`
- **Instancia Producción**: `go`
- **Cloudflare**: ✅ Conexión exitosa

## ⚠️ Observaciones Importantes

### 1. Nombre de Instancia de Producción

**Detectado**: La instancia de producción se configuró como `go`

**Recomendación**: 
- El nombre estándar debería ser `odoo-production` o similar
- El nombre `go` puede causar confusión con el usuario del sistema
- Si deseas cambiar esto, edita el archivo `.env`:
  ```bash
  nano /home/go/api-dev/.env
  # Cambiar: PROD_INSTANCE_NAME=go
  # Por:     PROD_INSTANCE_NAME=odoo-production
  ```

### 2. Conexión PostgreSQL

**Estado**: ⚠️ No se pudo verificar la conexión

**Posibles causas**:
1. PostgreSQL no está iniciado
2. Contraseña incorrecta
3. Usuario no tiene permisos

**Verificar**:
```bash
# Verificar que PostgreSQL está activo
sudo systemctl status postgresql

# Probar conexión manual
psql -h localhost -U go -d postgres

# Si necesitas cambiar la contraseña
sudo -u postgres psql
postgres=# ALTER USER go WITH PASSWORD 'nueva_contraseña';
```

**Actualizar .env si cambias la contraseña**:
```bash
nano /home/go/api-dev/.env
# Actualizar: DB_PASSWORD=nueva_contraseña
```

### 3. Variable CF_ZONE_NAME

**Nota**: En el `.env` se usa `DOMAIN_ROOT` pero algunos scripts antiguos pueden referenciar `CF_ZONE_NAME`

**Verificación**: Los scripts refactorizados ya usan correctamente:
```bash
CF_ZONE_NAME="${DOMAIN_ROOT}"
```

## 🔧 Correcciones Aplicadas

### Script validate-env.sh
✅ **Corregido**: Error al procesar el flag `--full`
- El script ahora maneja correctamente el flag `--full`
- Ya no intenta tratar `--full` como nombre de variable

## 📋 Próximos Pasos Recomendados

### 1. Verificar la Configuración Completa

```bash
cd /home/go/api-dev
source scripts/utils/validate-env.sh --full
```

Esto verificará:
- ✅ Todas las variables de entorno
- 📁 Rutas del sistema
- 🌐 Conectividad con Cloudflare
- 🗄️ Conectividad con PostgreSQL

### 2. Revisar y Ajustar el .env

```bash
# Ver el contenido (sin mostrar credenciales)
grep -v "PASSWORD\|TOKEN\|SECRET" /home/go/api-dev/.env

# Editar si es necesario
nano /home/go/api-dev/.env
```

**Variables críticas a revisar**:
- `PROD_INSTANCE_NAME`: Debería ser descriptivo (ej: `odoo-production`)
- `DB_PASSWORD`: Debe coincidir con la contraseña real de PostgreSQL
- `ODOO_ADMIN_PASSWORD`: Contraseña para el admin de Odoo

### 3. Desplegar el Panel de Control

Una vez que PostgreSQL esté funcionando:

```bash
cd /home/go/api-dev
./deploy.sh
```

### 4. Crear la Instancia de Producción

```bash
# Usar el nombre configurado en PROD_INSTANCE_NAME
./scripts/odoo/init-production.sh production

# O especificar un nombre personalizado
./scripts/odoo/init-production.sh nombre-personalizado
```

## 🐛 Solución de Problemas Comunes

### Error: "No se encontró el archivo .env"
```bash
# Ejecutar quickstart nuevamente
./quickstart.sh
```

### Error: "Variable X no está definida"
```bash
# Verificar que la variable existe en .env
grep "VARIABLE_NAME" .env

# Si no existe, agregarla
echo "VARIABLE_NAME=valor" >> .env
```

### Error: PostgreSQL no acepta la conexión
```bash
# Verificar el servicio
sudo systemctl status postgresql

# Reiniciar si es necesario
sudo systemctl restart postgresql

# Verificar configuración de pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Debe tener: local   all   go   md5
```

### Scripts no cargan las variables
```bash
# Asegurarse de que load-env.sh funciona
source /home/go/api-dev/scripts/utils/load-env.sh

# Verificar que PROJECT_ROOT está definido
echo $PROJECT_ROOT
```

## 📊 Estado del Sistema

### Archivos Creados:
- ✅ `/home/go/api-dev/.env` (permisos 600)
- ✅ `/home/go/api-dev/data/` (estructura creada)
- ✅ Scripts con permisos de ejecución

### Pendiente:
- ⏳ Verificar conexión PostgreSQL
- ⏳ Desplegar panel de control
- ⏳ Crear instancia de producción
- ⏳ Configurar servicios systemd

## 🔐 Seguridad

### Permisos del .env
```bash
# Verificar permisos (debe ser 600)
ls -la /home/go/api-dev/.env

# Si no es 600, corregir
chmod 600 /home/go/api-dev/.env
```

### Backup del .env
```bash
# Crear backup seguro del .env
cp /home/go/api-dev/.env /home/go/api-dev/.env.backup
chmod 600 /home/go/api-dev/.env.backup
```

## 📞 Contacto y Soporte

Si encuentras problemas:
1. Revisa los logs: `sudo journalctl -xe`
2. Verifica la documentación en `docs/`
3. Consulta la guía de migración: `docs/MIGRATION_GUIDE.md`

---

**Fecha**: $(date)
**Sistema**: API-DEV v2.0 (Refactorizado)
**Estado**: Configuración inicial completada ✅
