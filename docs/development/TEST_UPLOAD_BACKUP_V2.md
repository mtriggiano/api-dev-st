# Test de Upload de Backups V2

## ✅ Implementación Completada

### Backend
- ✅ Endpoint: `/api/backup/v2/instances/{instance_name}/upload`
- ✅ Método: `upload_backup()` en `BackupManagerV2`
- ✅ Validación de estructura (dump.sql + filestore)
- ✅ Conversión automática ZIP → TAR.GZ
- ✅ Logging detallado

### Frontend
- ✅ Botón "Subir Backup" en modal de lista de backups
- ✅ Modal de upload con drag & drop
- ✅ Progress tracking (velocidad, tiempo estimado)
- ✅ Validación de archivos (.tar.gz o .zip)
- ✅ API function: `backupV2.uploadBackup()`

## 🧪 Cómo Probar

### 1. Crear un Backup de Prueba

```bash
# Crear estructura de backup válida
mkdir -p /tmp/test_backup
cd /tmp/test_backup

# Crear dump.sql
echo "SELECT 1;" > dump.sql

# Crear filestore
mkdir -p filestore
echo "test file" > filestore/test.txt

# Crear tar.gz
tar -czf test_backup.tar.gz dump.sql filestore/

# Verificar
ls -lh test_backup.tar.gz
```

### 2. Probar desde el Panel Web

1. **Ir a Backups V2**: http://localhost/backups-v2
2. **Click en "Ver Backups (N)"** de cualquier instancia
3. **Click en botón "Subir Backup"** (morado, con ícono de upload)
4. **Arrastrar** el archivo `test_backup.tar.gz` o click en "Seleccionar archivo"
5. **Click en "Subir Backup"**
6. **Observar**:
   - Barra de progreso
   - Velocidad de subida
   - Tiempo estimado
   - Estado: "📤 Subiendo archivo..." → "🔍 Validando estructura..."
7. **Verificar** que aparezca en la lista de backups

### 3. Probar con cURL (Opcional)

```bash
# Obtener token de autenticación
TOKEN="your_jwt_token_here"

# Subir backup
curl -X POST http://localhost:5000/api/backup/v2/instances/production/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_backup/test_backup.tar.gz" \
  -v
```

### 4. Verificar en el Backend

```bash
# Ver logs
tail -f /home/mtg/api-dev/logs/gunicorn-error.log

# Buscar líneas como:
# 🚀 BACKUP_MANAGER_V2: Iniciando upload para instancia: production
# 📝 Tipo de archivo: TAR.GZ
# 💾 Guardando en: /tmp/upload_...
# 🔍 Validando estructura del TAR.GZ...
# ✅ Upload completado exitosamente
```

### 5. Verificar Archivo Guardado

```bash
# Listar backups de la instancia
ls -lh /home/mtg/api-dev/data/backups_v2/production/

# Debería aparecer algo como:
# backup_20251120_093000.tar.gz
```

## 🎯 Casos de Prueba

### ✅ Caso 1: Upload de TAR.GZ válido
- **Archivo**: `test_backup.tar.gz` con dump.sql + filestore
- **Resultado esperado**: ✅ Upload exitoso, archivo guardado

### ✅ Caso 2: Upload de ZIP válido
```bash
# Crear ZIP
cd /tmp/test_backup
zip -r test_backup.zip dump.sql filestore/
```
- **Resultado esperado**: ✅ Convertido a TAR.GZ automáticamente

### ❌ Caso 3: Archivo sin dump.sql
```bash
# Crear backup inválido
mkdir -p /tmp/invalid_backup
cd /tmp/invalid_backup
mkdir -p filestore
echo "test" > filestore/test.txt
tar -czf invalid_backup.tar.gz filestore/
```
- **Resultado esperado**: ❌ Error: "El backup no contiene dump.sql"

### ❌ Caso 4: Archivo con extensión incorrecta
- **Archivo**: `backup.txt`
- **Resultado esperado**: ❌ Error: "El archivo debe ser .tar.gz o .zip"

### ⚠️ Caso 5: Backup sin filestore
```bash
# Crear backup solo con dump
mkdir -p /tmp/nodump_backup
cd /tmp/nodump_backup
echo "SELECT 1;" > dump.sql
tar -czf nodump_backup.tar.gz dump.sql
```
- **Resultado esperado**: ⚠️ Warning en logs, pero upload exitoso

## 🐛 Troubleshooting

### Error: "No se proporcionó ningún archivo"
- **Causa**: FormData no contiene el campo 'file'
- **Solución**: Verificar que el frontend envía `formData.append('file', file)`

### Error: "El archivo debe ser .tar.gz o .zip"
- **Causa**: Extensión de archivo incorrecta
- **Solución**: Renombrar o crear archivo con extensión correcta

### Error: "El backup no contiene dump.sql"
- **Causa**: Estructura de backup inválida
- **Solución**: Asegurar que el archivo contiene `dump.sql` en la raíz

### Upload se queda en 0%
- **Causa**: Problema de red o CORS
- **Solución**: Verificar logs del backend, revisar configuración de NGINX

### Error 413: Payload Too Large
- **Causa**: Archivo muy grande
- **Solución**: Aumentar límites en:
  - Flask: `MAX_CONTENT_LENGTH`
  - NGINX: `client_max_body_size`
  - Gunicorn: `--limit-request-line`

## 📊 Validaciones Implementadas

### Backend
- ✅ Verificar que la instancia existe
- ✅ Validar extensión (.tar.gz o .zip)
- ✅ Validar estructura (dump.sql presente)
- ✅ Convertir ZIP a TAR.GZ si es necesario
- ✅ Guardar con timestamp único
- ✅ Actualizar configuración de instancia

### Frontend
- ✅ Validar extensión antes de subir
- ✅ Mostrar progreso en tiempo real
- ✅ Calcular velocidad y tiempo estimado
- ✅ Mostrar estado de validación
- ✅ Actualizar lista de backups al completar

## 🎉 Funcionalidades

### Drag & Drop
- ✅ Arrastrar archivos al área de upload
- ✅ Feedback visual al arrastrar
- ✅ Validación de extensión

### Progress Tracking
- ✅ Porcentaje de subida (0-100%)
- ✅ Bytes subidos / Total
- ✅ Velocidad (MB/s, KB/s)
- ✅ Tiempo estimado restante

### Conversión Automática
- ✅ ZIP → TAR.GZ transparente
- ✅ Validación de estructura
- ✅ Limpieza de archivos temporales

### Integración
- ✅ Se integra con lista de backups existente
- ✅ Actualiza automáticamente al completar
- ✅ Toast notifications
- ✅ Logging detallado

## 📝 Notas

- El sistema soporta archivos de hasta **1GB** (configurable)
- Los backups se guardan en `/home/mtg/api-dev/data/backups_v2/{instance}/`
- El nombre final es `backup_{timestamp}.tar.gz`
- Los archivos temporales se limpian automáticamente
- La validación es estricta: **debe** contener `dump.sql`
- El `filestore` es opcional pero se recomienda

## ✨ Mejoras Futuras (Opcional)

- [ ] Chunked upload para archivos muy grandes (>1GB)
- [ ] Validación de integridad (checksums)
- [ ] Preview del contenido del backup
- [ ] Historial de uploads
- [ ] Compresión adicional
- [ ] Encriptación de backups
