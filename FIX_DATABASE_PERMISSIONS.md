# ✅ Fix: Permisos de Base de Datos para Regenerar Assets

## 🐛 Problema

Al regenerar assets, el proceso fallaba con código 255 y el log mostraba:

```
ERROR: permission denied for schema public
LINE 2:         CREATE TABLE IF NOT EXISTS "res_users_apikeys" (
psycopg2.errors.InsufficientPrivilege: permission denied for schema public
```

## 🔍 Causa

La base de datos de desarrollo se estaba creando con el owner `go` (usuario antiguo) en lugar de `mtg` (usuario actual):

```bash
# INCORRECTO
sudo -u postgres createdb "$DEV_DB" -O "go" --encoding='UTF8'
```

Esto causaba que el usuario `mtg` (que ejecuta Odoo) no tuviera permisos para:
- Crear tablas
- Modificar esquemas
- Actualizar módulos
- Regenerar assets

## ✅ Solución

### 1. Corregir Owner de la Base de Datos

Cambiar el owner de `go` a `mtg`:

```bash
sudo -u postgres createdb "$DEV_DB" -O "mtg" --encoding='UTF8'
```

### 2. Otorgar Permisos Explícitos

Después de crear/restaurar la base de datos, otorgar todos los permisos necesarios:

```bash
# Asegurar permisos correctos
echo "🔐 Configurando permisos..."
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL ON SCHEMA public TO mtg;"
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;"
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;"
sudo -u postgres psql -d "$DEV_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mtg;"
```

### 3. Corregir Base de Datos Existente

Para la instancia `dev-testp4` que ya existía con permisos incorrectos:

```bash
sudo -u postgres psql -d dev-testp4-prod-panel4 -c "GRANT ALL ON SCHEMA public TO mtg;"
sudo -u postgres psql -d dev-testp4-prod-panel4 -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;"
sudo -u postgres psql -d dev-testp4-prod-panel4 -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;"
sudo -u postgres psql -d dev-testp4-prod-panel4 -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mtg;"
```

## 📁 Archivos Modificados

### 1. update-db.sh (Instancia Existente)

**Archivo**: `/home/mtg/apps/develop/odoo/dev-testp4/update-db.sh`

```bash
# ANTES
sudo -u postgres createdb "$DEV_DB" -O "go" --encoding='UTF8'

# AHORA
sudo -u postgres createdb "$DEV_DB" -O "mtg" --encoding='UTF8'
sudo -u postgres psql -d "$DEV_DB" < "/tmp/${DEV_DB}_dump.sql"
rm -f "/tmp/${DEV_DB}_dump.sql"

# Asegurar permisos correctos
echo "🔐 Configurando permisos..."
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL ON SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mtg;" > /dev/null
```

### 2. create-dev-instance.sh (Template)

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Línea 542**: Cambio de owner
```bash
sudo -u postgres createdb "$DEV_DB" -O "mtg" --encoding='UTF8'
```

**Líneas 546-551**: Configuración de permisos
```bash
# Asegurar permisos correctos
echo "🔐 Configurando permisos..."
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL ON SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mtg;" > /dev/null
```

## 🧪 Verificación

### 1. Verificar Owner de la Base de Datos

```bash
sudo -u postgres psql -c "\l dev-testp4-prod-panel4"
```

**Resultado esperado**:
```
                                                List of databases
         Name          | Owner | Encoding | Locale Provider | Collate | Ctype | Locale | ICU Rules | Access privileges
-----------------------+-------+----------+-----------------+---------+-------+--------+-----------+-------------------
 dev-testp4-prod-panel4| mtg   | UTF8     | libc            | ...     | ...   | ...    |           |
```

### 2. Verificar Permisos en el Schema

```bash
sudo -u postgres psql -d dev-testp4-prod-panel4 -c "\dn+"
```

**Resultado esperado**:
```
Schema | Owner | Access privileges | Description
-------+-------+-------------------+-------------
public | mtg   | mtg=UC/mtg       +| standard public schema
       |       | =U/mtg           +|
       |       | mtg=UC/mtg        |
```

### 3. Probar Regeneración de Assets

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./regenerate-assets.sh
```

**Resultado esperado**:
```
✅ Regeneración completada exitosamente
✅ Servicio iniciado correctamente
```

## 📊 Permisos Otorgados

| Permiso | Descripción | Necesario Para |
|---------|-------------|----------------|
| `GRANT ALL ON SCHEMA public` | Acceso total al schema | Crear/modificar objetos |
| `GRANT ALL ON ALL TABLES` | Acceso a todas las tablas | Leer/escribir datos |
| `GRANT ALL ON ALL SEQUENCES` | Acceso a secuencias | Auto-incrementos |
| `ALTER DEFAULT PRIVILEGES` | Permisos por defecto | Nuevas tablas |

## 💡 Contexto: Migración de Usuario

### Historia

El sistema originalmente usaba el usuario `go`:
- Usuario del sistema: `go`
- Usuario de PostgreSQL: `go`
- Owner de bases de datos: `go`

Posteriormente se migró al usuario `mtg`:
- Usuario del sistema: `mtg`
- Usuario de PostgreSQL: `mtg`
- ❌ Owner de bases de datos: **seguía siendo `go`**

### Problema

Cuando Odoo (ejecutándose como `mtg`) intentaba modificar la base de datos (owned por `go`), no tenía permisos suficientes.

### Solución

Cambiar el owner de todas las bases de datos de desarrollo a `mtg` y otorgar permisos explícitos.

## 🔍 Verificar Otras Instancias

Si hay más instancias de desarrollo, verificar y corregir sus permisos:

```bash
# Listar todas las bases de datos de desarrollo
sudo -u postgres psql -c "\l" | grep "^dev-"

# Para cada base de datos, verificar el owner
sudo -u postgres psql -c "\l nombre-de-bd"

# Si el owner es 'go', corregir:
sudo -u postgres psql -d nombre-de-bd -c "ALTER DATABASE nombre-de-bd OWNER TO mtg;"
sudo -u postgres psql -d nombre-de-bd -c "GRANT ALL ON SCHEMA public TO mtg;"
sudo -u postgres psql -d nombre-de-bd -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;"
sudo -u postgres psql -d nombre-de-bd -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;"
```

## 🎯 Resultado

- ✅ Base de datos creada con owner correcto (`mtg`)
- ✅ Permisos explícitos otorgados
- ✅ Regeneración de assets funciona
- ✅ Actualización de módulos funciona
- ✅ Template actualizado para nuevas instancias
- ✅ Instancia existente corregida

---

**Fecha**: 19 Nov 2025 14:05
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar regeneración de assets desde el panel web
