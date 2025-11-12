# 🔗 Integración GitHub para Custom Addons

Esta guía explica cómo usar la integración de GitHub para gestionar el control de versiones de tus custom addons en instancias de desarrollo de Odoo.

## 📋 Índice

1. [Requisitos](#requisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Flujo de Trabajo](#flujo-de-trabajo)
4. [Endpoints API](#endpoints-api)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Requisitos

### 1. Git Instalado en el Servidor

**CRÍTICO:** El servidor debe tener Git instalado y accesible en `/usr/bin/git`.

```bash
# Verificar instalación de Git
which git
git --version

# Si no está instalado (Ubuntu/Debian):
sudo apt update
sudo apt install git -y

# Verificar que esté en /usr/bin/git
ls -la /usr/bin/git
```

⚠️ **Nota importante:** El sistema usa la ruta absoluta `/usr/bin/git` para evitar problemas con el PATH del proceso de Gunicorn. Si Git está instalado en otra ubicación, deberás modificar `backend/services/git_manager.py`.

### 2. Token de Acceso Personal de GitHub

Necesitas crear un Personal Access Token (PAT) en GitHub con los siguientes permisos:

1. Ve a GitHub → **Settings** (tu perfil)
2. Scroll hasta el final → **Developer settings**
3. Click en **Personal access tokens**
4. Click en **Tokens (classic)**
5. Click en **Generate new token**
6. Click en **Generate new token (classic)**
7. Dale un nombre descriptivo (ej: "Odoo Dev Panel")
8. Selecciona una expiración (recomendado: 90 días o sin expiración)
9. Selecciona los siguientes scopes:
   - ✅ **`repo`** (acceso completo a repositorios privados) - **IMPORTANTE: Marca la casilla principal "repo" que automáticamente marca todas las sub-opciones**
   - ✅ **`user:email`** (acceso a tu email)
10. Scroll hasta el final y click en **Generate token**
11. **COPIA EL TOKEN INMEDIATAMENTE** y guárdalo en un lugar seguro (no podrás verlo de nuevo)
    - El token debe empezar con `ghp_` seguido de caracteres alfanuméricos
    - Ejemplo: `ghp_1234567890abcdefghijklmnopqrstuvwxyz`

### 2. Repositorio GitHub

- Crea un repositorio en GitHub para tus custom addons
- Puede ser público o privado
- Asegúrate de tener permisos de escritura

### 3. Carpeta Local

- Identifica la ruta de la carpeta de custom addons en tu instancia de desarrollo
- Ejemplo: `/home/go/apps/develop/odoo/dev-mi-instancia/custom-addons`

---

## ⚙️ Configuración Inicial

### Paso 1: Verificar Token

Primero verifica que tu token de GitHub sea válido:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/verify-token \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "ghp_tu_token_de_github"
  }'
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "username": "tu-usuario-github",
  "name": "Tu Nombre",
  "email": "tu@email.com",
  "avatar_url": "https://avatars.githubusercontent.com/..."
}
```

### Paso 2: Crear Configuración

Vincula tu cuenta de GitHub con una instancia:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/config \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mi-instancia",
    "github_token": "ghp_tu_token_de_github",
    "repo_owner": "tu-usuario-o-org",
    "repo_name": "nombre-del-repo",
    "repo_branch": "main",
    "local_path": "/home/go/apps/develop/odoo/dev-mi-instancia/custom-addons"
  }'
```

### Paso 3: Inicializar Repositorio

Si la carpeta aún no es un repositorio Git:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/init-repo \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mi-instancia"
  }'
```

---

## 🔄 Flujo de Trabajo

### 1. Ver Estado del Repositorio

Verifica qué archivos han cambiado:

```bash
curl -X GET https://api-dev.hospitalprivadosalta.ar/api/github/status/dev-mi-instancia \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Respuesta:**
```json
{
  "success": true,
  "branch": "main",
  "remote_url": "https://github.com/usuario/repo.git",
  "has_changes": true,
  "changes": [
    {
      "status": "M",
      "file": "mi_modulo/__manifest__.py"
    },
    {
      "status": "A",
      "file": "mi_modulo/models/nuevo_modelo.py"
    }
  ],
  "last_commit": {
    "hash": "abc123...",
    "author": "Tu Nombre",
    "email": "tu@email.com",
    "timestamp": "1698765432",
    "message": "Último commit"
  }
}
```

### 2. Crear Commit

Guarda tus cambios localmente:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/commit \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mi-instancia",
    "message": "Agregado nuevo módulo de inventario",
    "author_name": "Tu Nombre",
    "author_email": "tu@email.com"
  }'
```

### 3. Push a GitHub

Sube tus commits al repositorio remoto:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/push \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mi-instancia"
  }'
```

### 4. Pull desde GitHub

Descarga cambios del repositorio remoto:

```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/pull \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mi-instancia"
  }'
```

---

## 📡 Endpoints API

### Autenticación y Configuración

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/github/verify-token` | Verifica un token de GitHub |
| GET | `/api/github/repos` | Lista repositorios del usuario (requiere header `X-GitHub-Token`) |
| GET | `/api/github/config` | Lista configuraciones del usuario |
| GET | `/api/github/config/:instance` | Obtiene configuración de una instancia |
| POST | `/api/github/config` | Crea/actualiza configuración |
| DELETE | `/api/github/config/:instance` | Elimina configuración |
| POST | `/api/github/config/:instance/reset` | **NUEVO** Resetea completamente la configuración (limpia token) |
| POST | `/api/github/config/:instance/reconfigure` | **NUEVO** Reconfigura con un nuevo token |

### Operaciones Git

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/github/init-repo` | Inicializa repositorio Git |
| GET | `/api/github/status/:instance` | Estado del repositorio |
| POST | `/api/github/commit` | Crea un commit |
| POST | `/api/github/push` | Push al remoto |
| POST | `/api/github/pull` | Pull del remoto |
| GET | `/api/github/history/:instance` | Historial de commits |
| GET | `/api/github/diff/:instance` | Diff de cambios |

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Workflow Completo

```bash
# 1. Verificar cambios
curl -X GET https://api-dev.hospitalprivadosalta.ar/api/github/status/dev-juan \
  -H "Authorization: Bearer $JWT_TOKEN"

# 2. Ver diferencias
curl -X GET "https://api-dev.hospitalprivadosalta.ar/api/github/diff/dev-juan" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 3. Crear commit
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/commit \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-juan",
    "message": "Implementado módulo de reportes"
  }'

# 4. Push a GitHub
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/push \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instance_name": "dev-juan"}'
```

### Ejemplo 2: Ver Historial

```bash
# Ver últimos 10 commits
curl -X GET "https://api-dev.hospitalprivadosalta.ar/api/github/history/dev-juan?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Ejemplo 3: Listar Repositorios

```bash
# Listar todos tus repositorios
curl -X GET https://api-dev.hospitalprivadosalta.ar/api/github/repos \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "X-GitHub-Token: ghp_tu_token"
```

---

## 🐛 Solución de Problemas

### Error: "Token de GitHub inválido"

**Causa:** El token ha expirado o no tiene los permisos correctos.

**Solución:**
1. Genera un nuevo token en GitHub
2. Asegúrate de incluir el scope `repo`
3. Actualiza la configuración con el nuevo token

### Error: "La carpeta ya es un repositorio Git"

**Causa:** La carpeta ya tiene un `.git` inicializado.

**Solución:**
- Si quieres mantener el repo existente, no uses `init-repo`
- Si quieres empezar de cero: `rm -rf /ruta/.git` y luego `init-repo`

### Error: "No es un repositorio Git"

**Causa:** La carpeta no tiene Git inicializado.

**Solución:**
```bash
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/init-repo \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instance_name": "dev-mi-instancia"}'
```

### Error: "[Errno 2] No such file or directory: 'git'"

**Causa:** Git no está instalado o no está en la ruta esperada (`/usr/bin/git`).

**Solución:**
```bash
# 1. Verificar si Git está instalado
which git

# 2. Si no está instalado, instalarlo
sudo apt update
sudo apt install git -y

# 3. Verificar que esté en /usr/bin/git
ls -la /usr/bin/git

# 4. Reiniciar el servicio de API
sudo systemctl restart server-panel-api

# 5. Verificar logs
sudo journalctl -u server-panel-api -n 50
```

⚠️ **Nota técnica:** El sistema usa `/usr/bin/git` como ruta absoluta porque el proceso de Gunicorn no hereda el PATH completo del sistema. Si Git está instalado en otra ubicación (ej: `/usr/local/bin/git`), deberás modificar la línea 28 de `backend/services/git_manager.py`:

```python
# Cambiar de:
command[0] = '/usr/bin/git'

# A tu ruta personalizada:
command[0] = '/ruta/a/tu/git'
```

### Error al hacer Push: "Authentication failed"

**Causa:** El token no tiene permisos de escritura o ha expirado.

**Solución:**
1. Verifica que el token tenga scope `repo`
2. Verifica que tengas permisos de escritura en el repositorio
3. Actualiza el token en la configuración

### Conflictos al hacer Pull

**Causa:** Hay cambios locales que conflictúan con el remoto.

**Solución:**
1. Haz commit de tus cambios locales primero
2. Luego haz pull
3. Si hay conflictos, resuélvelos manualmente en el servidor

---

## 🔒 Seguridad

### Mejores Prácticas

1. **Tokens de Acceso:**
   - Usa tokens con permisos mínimos necesarios
   - Rota los tokens periódicamente
   - No compartas tokens entre usuarios

2. **Repositorios:**
   - Usa repositorios privados para código propietario
   - Configura branch protection rules en GitHub
   - Habilita 2FA en tu cuenta de GitHub

3. **Auditoría:**
   - Todas las operaciones Git se registran en los logs
   - Revisa regularmente el historial de acciones

### Nota sobre Almacenamiento de Tokens

⚠️ **Importante:** Los tokens se almacenan en la base de datos. En un entorno de producción, deberías:
- Encriptar los tokens antes de guardarlos
- Usar un servicio de gestión de secretos (como HashiCorp Vault)
- Implementar rotación automática de tokens

---

## 📚 Recursos Adicionales

- [Documentación de GitHub API](https://docs.github.com/en/rest)
- [Crear Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)

---

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs de la API: `sudo journalctl -u server-panel-api -f`
2. Verifica los logs de acciones en el panel
3. Consulta esta documentación
4. Contacta al administrador del sistema

---

## 🚀 Webhooks y Auto-Deploy (Nuevo)

### Configuración de Webhooks para Producción

Las instancias de producción pueden configurarse para recibir webhooks de GitHub y hacer auto-deploy automáticamente cuando se hace push a la rama `main`.

#### Configurar Webhook

1. **Desde el Panel Web**:
   - Ve a la instancia de producción
   - Click en el botón **GitHub**
   - Si ya está conectado, verás la opción **"Configurar Webhook"**
   - Activa **"Auto-deploy en push a main"**
   - Opcionalmente activa **"Actualizar módulos Odoo automáticamente"**
   - Click en **"Guardar Configuración"**

2. **Copiar URL y Secret del Webhook**:
   - Después de guardar, verás:
     - **Webhook URL**: `https://tu-dominio.ar/api/github/webhook/production`
     - **Webhook Secret**: Un token secreto generado automáticamente
   - Usa los botones de copiar para copiar cada valor

3. **Configurar en GitHub**:
   - Ve a tu repositorio en GitHub
   - **Settings** → **Webhooks** → **Add webhook**
   - **Payload URL**: Pega la URL del webhook
   - **Content type**: Selecciona `application/x-www-form-urlencoded` o `application/json`
   - **Secret**: Pega el secret del webhook
   - **Which events**: Selecciona "Just the push event"
   - **Active**: ✅ Marcado
   - Click en **Add webhook**

4. **Probar el Webhook**:
   - En el panel, click en **"Probar Webhook"**
   - Verifica que el deploy se ejecute correctamente
   - En GitHub, ve a **Settings** → **Webhooks** → Click en tu webhook
   - En **Recent Deliveries** verás el evento `ping` con status 200

#### Cómo Funciona el Auto-Deploy

Cuando haces push a `main`:

1. **GitHub envía webhook** → Tu servidor
2. **Validación de signature** → Verifica que viene de GitHub
3. **Git pull** → Descarga los cambios
4. **Actualizar módulos** (opcional) → Detiene Odoo, actualiza módulos, reinicia
5. **Log del deploy** → Se guarda en la base de datos

#### Ver Logs de Deploy

1. Ve a la instancia → Click en **"Logs"**
2. Selecciona la pestaña **"Git/Deploy"**
3. Verás el historial completo:
   ```
   [12/11/2025 23:05:00] ✅ webhook_autodeploy: Deploy exitoso: Fix bug en módulo X (System)
   [12/11/2025 22:30:00] ✅ test_webhook: Test deploy exitoso (admin)
   ```

#### Monitorear Commit Actual

Debajo del botón de GitHub en cada instancia verás un badge con el hash del commit actual:
- **Hash corto**: `a1b2c3d`
- **Tooltip**: Mensaje completo del commit

#### Endpoints de Webhook

- **POST** `/api/github/webhook/config/<instance_name>` - Configurar webhook
- **POST** `/api/github/webhook/<instance_name>` - Recibir webhook de GitHub
- **POST** `/api/github/webhook/test/<instance_name>` - Probar webhook manualmente
- **GET** `/api/github/current-commit/<instance_name>` - Obtener commit actual
- **GET** `/api/github/deploy-logs/<instance_name>` - Obtener logs de deploy

#### Seguridad

- **HMAC SHA256**: Todos los webhooks se validan con signature
- **Secret único**: Cada instancia tiene su propio secret
- **Logs auditables**: Todos los deploys se registran con usuario y timestamp

---

**Última actualización:** 2025-11-12  
**Versión:** 3.0 - Agregado soporte para webhooks, auto-deploy, y monitoreo de commits
