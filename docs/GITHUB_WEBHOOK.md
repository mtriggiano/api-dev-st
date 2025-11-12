# 🔔 GitHub Webhook - Auto-Deploy

Documentación completa del sistema de webhooks de GitHub para auto-despliegue en producción.

---

## 📋 Índice

1. [Descripción](#descripción)
2. [Cómo Funciona](#cómo-funciona)
3. [Configuración](#configuración)
4. [Endpoints API](#endpoints-api)
5. [Configurar Webhook en GitHub](#configurar-webhook-en-github)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Descripción

El sistema de webhooks permite que cuando hagas un `push` o `merge` a la rama `main` en GitHub, automáticamente se ejecute en el servidor:

1. **Git Pull**: Descarga los últimos cambios
2. **Actualización de Módulos** (opcional): Actualiza los módulos de Odoo
3. **Reinicio de Servicio** (opcional): Reinicia el servicio de Odoo

### Diferencias entre Desarrollo y Producción

| Característica | Desarrollo (`dev-*`) | Producción |
|----------------|---------------------|------------|
| Rama por defecto | Nombre de instancia (ej: `dev-mtg`) | `main` |
| Auto-deploy | Opcional | Recomendado |
| Update módulos | Manual | Automático (opcional) |
| Webhook | No recomendado | Sí |

---

## 🔄 Cómo Funciona

```
┌─────────────┐
│   GitHub    │
│  (Push/PR)  │
└──────┬──────┘
       │
       │ Webhook HTTP POST
       ▼
┌─────────────────┐
│   API-DEV       │
│  /webhook/...   │
└────────┬────────┘
         │
         │ 1. Valida signature
         │ 2. Verifica rama
         │ 3. Extrae info commit
         ▼
┌─────────────────┐
│  Deploy Manager │
└────────┬────────┘
         │
         ├─► Git Pull
         │
         ├─► Update Modules (si está habilitado)
         │
         └─► Restart Service
```

---

## ⚙️ Configuración

### Paso 1: Configurar Webhook en API-DEV

```bash
curl -X POST https://api-dev.tudominio.com/api/github/webhook/config/INSTANCIA \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_deploy": true,
    "update_modules": true
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Webhook configurado exitosamente",
  "webhook_url": "https://api-dev.tudominio.com/api/github/webhook/INSTANCIA",
  "webhook_secret": "abc123...xyz789",
  "config": {
    "instance_name": "INSTANCIA",
    "instance_type": "production",
    "auto_deploy": true,
    "update_modules_on_deploy": true,
    "repo_branch": "main"
  }
}
```

⚠️ **IMPORTANTE**: Guarda el `webhook_secret` - lo necesitarás para configurar GitHub.

### Paso 2: Configurar Webhook en GitHub

1. Ve a tu repositorio en GitHub
2. Click en **Settings** → **Webhooks** → **Add webhook**
3. Configura:
   - **Payload URL**: `https://api-dev.tudominio.com/api/github/webhook/INSTANCIA`
   - **Content type**: `application/json`
   - **Secret**: El `webhook_secret` que obtuviste en el paso 1
   - **Which events**: Solo `push` events
   - **Active**: ✅ Marcado
4. Click en **Add webhook**

### Paso 3: Probar el Webhook

```bash
curl -X POST https://api-dev.tudominio.com/api/github/webhook/test/INSTANCIA \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📡 Endpoints API

### 1. Configurar Webhook

**POST** `/api/github/webhook/config/<instance_name>`

Configura el webhook para una instancia.

**Headers:**
- `Authorization: Bearer JWT_TOKEN`
- `Content-Type: application/json`

**Body:**
```json
{
  "auto_deploy": true,
  "update_modules": true
}
```

**Respuesta:**
```json
{
  "success": true,
  "webhook_url": "https://...",
  "webhook_secret": "...",
  "config": {...}
}
```

### 2. Recibir Webhook de GitHub

**POST** `/api/github/webhook/<instance_name>`

Endpoint público que recibe los webhooks de GitHub.

**Headers (enviados por GitHub):**
- `X-Hub-Signature-256`: Firma HMAC del payload
- `X-GitHub-Event`: Tipo de evento (debe ser `push`)
- `Content-Type: application/json`

**Body (enviado por GitHub):**
```json
{
  "ref": "refs/heads/main",
  "commits": [...],
  "pusher": {...},
  "repository": {...}
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Deploy completado exitosamente",
  "commit_info": {
    "branch": "main",
    "commits_count": 1,
    "last_commit": {...}
  },
  "deploy_result": {
    "pull": {...},
    "update_modules": {...}
  }
}
```

### 3. Probar Webhook

**POST** `/api/github/webhook/test/<instance_name>`

Prueba el webhook manualmente sin esperar un push de GitHub.

**Headers:**
- `Authorization: Bearer JWT_TOKEN`

**Respuesta:**
```json
{
  "success": true,
  "message": "Test completado",
  "deploy_result": {...}
}
```

---

## 🔧 Configurar Webhook en GitHub (Detallado)

### Opción 1: Desde la Interfaz Web

1. **Ir al repositorio**
   ```
   https://github.com/USUARIO/REPOSITORIO
   ```

2. **Settings → Webhooks → Add webhook**

3. **Configurar:**
   - **Payload URL**: 
     ```
     https://api-dev.tudominio.com/api/github/webhook/NOMBRE_INSTANCIA
     ```
   - **Content type**: `application/json`
   - **Secret**: Tu `webhook_secret`
   - **SSL verification**: Enable SSL verification
   - **Which events would you like to trigger this webhook?**
     - ☑️ Just the `push` event
   - **Active**: ✅

4. **Add webhook**

### Opción 2: Usando la API de GitHub

```bash
curl -X POST https://api.github.com/repos/USUARIO/REPO/hooks \
  -H "Authorization: Bearer GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web",
    "active": true,
    "events": ["push"],
    "config": {
      "url": "https://api-dev.tudominio.com/api/github/webhook/INSTANCIA",
      "content_type": "json",
      "secret": "TU_WEBHOOK_SECRET",
      "insecure_ssl": "0"
    }
  }'
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Configurar Auto-Deploy para Producción

```bash
# 1. Configurar webhook
curl -X POST https://api-dev.tudominio.com/api/github/webhook/config/produccion \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_deploy": true,
    "update_modules": true
  }'

# Guardar el webhook_secret de la respuesta

# 2. Ir a GitHub y configurar el webhook con el secret

# 3. Hacer un push a main
git add .
git commit -m "Update modules"
git push origin main

# 4. Ver logs en API-DEV
curl -X GET https://api-dev.tudominio.com/api/logs \
  -H "Authorization: Bearer $JWT_TOKEN" \
  | jq '.logs[] | select(.action == "webhook_autodeploy")'
```

### Ejemplo 2: Probar Webhook Manualmente

```bash
# Probar sin hacer push a GitHub
curl -X POST https://api-dev.tudominio.com/api/github/webhook/test/produccion \
  -H "Authorization: Bearer $JWT_TOKEN" \
  | jq '.'
```

### Ejemplo 3: Deshabilitar Auto-Deploy

```bash
curl -X POST https://api-dev.tudominio.com/api/github/webhook/config/produccion \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_deploy": false,
    "update_modules": false
  }'
```

---

## 🐛 Solución de Problemas

### Error: "Signature inválida"

**Causa:** El `webhook_secret` no coincide.

**Solución:**
1. Verifica que el secret en GitHub sea exactamente el mismo que en API-DEV
2. No debe tener espacios al inicio o final
3. Regenera el secret si es necesario:
   ```bash
   curl -X POST .../webhook/config/INSTANCIA \
     -d '{"auto_deploy": true, "update_modules": true}'
   ```

### Error: "Configuración no encontrada"

**Causa:** No existe una configuración de GitHub para esa instancia.

**Solución:**
1. Primero conecta la instancia con GitHub desde el panel
2. Luego configura el webhook

### Error: "Evento ignorado"

**Causa:** El webhook se disparó por un evento que no es `push`.

**Solución:**
- Esto es normal, el sistema solo procesa `push` events
- Verifica en GitHub que solo esté marcado "push" en la configuración del webhook

### Error: "Rama ignorada"

**Causa:** El push fue a una rama diferente a la configurada.

**Solución:**
- Para producción, asegúrate de hacer push a `main`
- Para desarrollo, usa la rama con el nombre de la instancia

### Webhook no se dispara

**Solución:**
1. Verifica en GitHub → Settings → Webhooks → Recent Deliveries
2. Revisa el status code de las entregas
3. Verifica que la URL sea accesible públicamente
4. Revisa los logs de API-DEV:
   ```bash
   sudo journalctl -u server-panel-api -f
   ```

### Módulos no se actualizan

**Solución:**
1. Verifica que `update_modules_on_deploy` esté en `true`
2. Verifica permisos del usuario `odoo`
3. Revisa logs de Odoo:
   ```bash
   sudo journalctl -u odoo-INSTANCIA -f
   ```

---

## 🔒 Seguridad

### Mejores Prácticas

1. **Usa HTTPS**: Siempre configura el webhook con HTTPS
2. **Valida Signature**: El sistema valida automáticamente la firma HMAC
3. **Limita Eventos**: Solo habilita `push` events
4. **Monitorea Logs**: Revisa regularmente los logs de deploy
5. **Backup**: Siempre ten backups antes de habilitar auto-deploy

### Validación de Signature

El sistema valida automáticamente que el webhook venga de GitHub usando HMAC-SHA256:

```python
expected_signature = 'sha256=' + hmac.new(
    webhook_secret.encode(),
    payload,
    hashlib.sha256
).hexdigest()

if not hmac.compare_digest(signature, expected_signature):
    return 401  # Unauthorized
```

---

## 📊 Monitoreo

### Ver Últimos Deploys

```bash
curl -X GET https://api-dev.tudominio.com/api/logs \
  -H "Authorization: Bearer $JWT_TOKEN" \
  | jq '.logs[] | select(.action == "webhook_autodeploy") | {
      timestamp,
      instance_name,
      details,
      status
    }'
```

### Ver Configuración Actual

```bash
curl -X GET https://api-dev.tudominio.com/api/github/config/INSTANCIA \
  -H "Authorization: Bearer $JWT_TOKEN" \
  | jq '{
      auto_deploy,
      update_modules_on_deploy,
      last_deploy_at,
      repo_branch
    }'
```

---

## 📚 Recursos Adicionales

- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [Securing Webhooks](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)
- [GitHub Integration](GITHUB_INTEGRATION.md)

---

**Última actualización:** 2025-11-12  
**Versión:** 2.2.0 - Sistema de Webhooks y Auto-Deploy
