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

### 1. Token de Acceso Personal de GitHub

Necesitas crear un Personal Access Token (PAT) en GitHub con los siguientes permisos:

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click en "Generate new token (classic)"
3. Selecciona los siguientes scopes:
   - ✅ `repo` (acceso completo a repositorios privados)
   - ✅ `user:email` (acceso a tu email)
4. Genera el token y **guárdalo en un lugar seguro** (no podrás verlo de nuevo)

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

**Última actualización:** 2025-10-30
