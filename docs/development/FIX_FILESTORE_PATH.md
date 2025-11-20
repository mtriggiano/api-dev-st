# ✅ Fix: Ruta de Filestore Incorrecta

## 🐛 Problema

Al sincronizar filestore desde el panel web, mostraba:

```
📁 Sincronizando filestore...
⚠️  No se encontró filestore de producción en /home/go/.local/share/Odoo/filestore/prod-panel4
```

### Causa

Los scripts estaban usando la ruta del usuario `go` en lugar del usuario `mtg`:
- ❌ Ruta incorrecta: `/home/go/.local/share/Odoo/filestore`
- ✅ Ruta correcta: `/home/mtg/.local/share/Odoo/filestore`

## ✅ Solución

### 1. Scripts Existentes Corregidos

**Archivos modificados en `dev-testp4`**:

#### sync-filestore.sh
```bash
# ANTES
FILESTORE_BASE="/home/go/.local/share/Odoo/filestore"

# AHORA
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
```

#### update-db.sh
```bash
# ANTES
FILESTORE_BASE="/home/go/.local/share/Odoo/filestore"

# AHORA
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
```

### 2. Templates Actualizados

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Líneas corregidas**:
- Línea 266: Copia inicial de filestore durante creación
- Línea 547: Template de `update-db.sh`
- Línea 691: Template de `sync-filestore.sh`

Todas ahora usan: `/home/mtg/.local/share/Odoo/filestore`

## 📊 Verificación de Rutas

### Filestore de Producción
```bash
$ ls -la /home/mtg/.local/share/Odoo/filestore/ | grep prod-panel
drwxrwxr-x 207 mtg mtg 4096 Nov 18 19:22 prod-panel1
drwxrwxr-x 208 mtg mtg 4096 Nov 18 20:16 prod-panel3
drwxrwxr-x 208 mtg mtg 4096 Nov 18 23:41 prod-panel4
```

### Filestore de Desarrollo
```bash
$ ls -la /home/mtg/.local/share/Odoo/filestore/ | grep dev-
drwxrwxr-x  15 mtg mtg 4096 Nov 19 08:21 dev-mt4p-prod-panel4
drwxrwxr-x  15 mtg mtg 4096 Nov 19 08:45 dev-mtgp4v2-prod-panel4
drwxrwxr-x  24 mtg mtg 4096 Nov 19 09:16 dev-testp4-prod-panel4
```

## 🎯 Resultado

Ahora cuando se sincroniza el filestore:

```
📁 Sincronizando filestore...
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
PROD_FILESTORE="/home/mtg/.local/share/Odoo/filestore/prod-panel4"
DEV_FILESTORE="/home/mtg/.local/share/Odoo/filestore/dev-testp4-prod-panel4"

✅ Filestore encontrado
✅ Sincronización exitosa
✅ X archivos copiados
```

## 🧪 Prueba

### Desde Panel Web

1. Ir a "Instancias"
2. Clic en ⚙️ de `dev-testp4`
3. Seleccionar "Sincronizar Filestore"
4. Clic en "Sincronizar"

**Resultado esperado**:
```
📁 Sincronizando filestore desde producción...
   Producción: prod-panel4
   Desarrollo: dev-testp4-prod-panel4
⏹️  Deteniendo servicio Odoo...
📁 Sincronizando filestore...
✅ Filestore sincronizado (XXXX archivos)
▶️  Iniciando servicio Odoo...
✅ Filestore sincronizado correctamente.
```

### Desde Terminal

```bash
cd /home/mtg/apps/develop/odoo/dev-testp4
./sync-filestore.sh
```

**Resultado esperado**:
```
Confirmar sincronización (s/n): s
⏹️  Deteniendo servicio Odoo...
📁 Sincronizando filestore...
✅ Filestore sincronizado (XXXX archivos)
▶️  Iniciando servicio Odoo...
✅ Filestore sincronizado correctamente.
```

## 📁 Archivos Modificados

### Instancia Existente
```
/home/mtg/apps/develop/odoo/dev-testp4/
├── sync-filestore.sh           ✅ Ruta corregida
└── update-db.sh                ✅ Ruta corregida
```

### Template
```
/home/mtg/api-dev/scripts/odoo/
└── create-dev-instance.sh      ✅ 3 ocurrencias corregidas
```

## 💡 Contexto

### ¿Por qué estaba en /home/go?

El sistema originalmente usaba el usuario `go` para ejecutar Odoo. Posteriormente se migró al usuario `mtg`, pero algunos scripts conservaron las rutas antiguas.

### Rutas Correctas del Sistema

```
Usuario Odoo: mtg
Home: /home/mtg
Filestore: /home/mtg/.local/share/Odoo/filestore/
Instancias Producción: /home/mtg/apps/production/odoo/
Instancias Desarrollo: /home/mtg/apps/develop/odoo/
Scripts: /home/mtg/api-dev/scripts/
```

## 🔍 Otros Scripts a Revisar

Verificar si hay más referencias a `/home/go` en otros scripts:

```bash
grep -r "/home/go" /home/mtg/api-dev/scripts/
```

Si hay más ocurrencias, deberían ser corregidas también.

## 📊 Resumen

| Componente | Antes | Ahora | Estado |
|------------|-------|-------|--------|
| sync-filestore.sh (instancia) | /home/go | /home/mtg | ✅ Corregido |
| update-db.sh (instancia) | /home/go | /home/mtg | ✅ Corregido |
| create-dev-instance.sh (línea 266) | /home/go | /home/mtg | ✅ Corregido |
| create-dev-instance.sh (línea 547) | /home/go | /home/mtg | ✅ Corregido |
| create-dev-instance.sh (línea 691) | /home/go | /home/mtg | ✅ Corregido |

---

**Fecha**: 19 Nov 2025 12:45
**Estado**: ✅ CORREGIDO
**Próximo paso**: Probar sincronización de filestore desde el panel web
