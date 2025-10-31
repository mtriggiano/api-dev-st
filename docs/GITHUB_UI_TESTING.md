# 🧪 Guía de Pruebas - Integración GitHub UI

## ✅ Implementación Completada

Se ha implementado un botón de GitHub en la interfaz web que simplifica todo el proceso de conexión con repositorios. Ahora solo necesitas:

1. **Token de GitHub**: Tu token personal de GitHub (ghp_...)
2. **URL del Repositorio**: La URL de tu repositorio en GitHub
3. **Instancia**: El nombre de tu instancia de desarrollo

---

## 🎯 Cómo Probar

### Paso 1: Acceder al Panel Web

1. Abre tu navegador en: **https://api-dev.hospitalprivadosalta.ar**
2. Inicia sesión con tus credenciales

### Paso 2: Ir a Instancias de Desarrollo

1. En el menú lateral, haz clic en **"Instancias"**
2. Busca la sección **"Desarrollo"**
3. Localiza tu instancia **dev-mtg**

### Paso 3: Conectar con GitHub

1. En la tarjeta de tu instancia de desarrollo, verás un botón **"GitHub"** con el ícono de GitHub
2. Haz clic en el botón **"GitHub"**
3. Se abrirá un modal con dos campos:
   - **Token de GitHub**: Pega tu token personal de GitHub
   - **URL del Repositorio**: Pega la URL de tu repositorio (ej: `https://github.com/usuario/repositorio`)
4. Haz clic en **"Conectar"**

### Paso 4: Proceso Automático

El sistema hará automáticamente:

1. ✅ **Verificar** que el token sea válido
2. ✅ **Crear configuración** en la base de datos con:
   - Repositorio: `mtriggiano/imac-dev`
   - Rama: `dev-mtg` (se crea automáticamente con el nombre de tu instancia)
   - Ruta local: `/home/go/apps/develop/odoo/dev-mtg/custom_addons`
3. ✅ **Inicializar** el repositorio Git en la carpeta
4. ✅ **Conectar** el remoto con GitHub
5. ✅ **Crear rama** `dev-mtg` si no existe

### Paso 5: Verificar Conexión

Una vez completado, verás un mensaje de éxito. Puedes verificar que todo funciona:

```bash
# Conectarse al servidor
ssh usuario@servidor

# Ir a la carpeta de custom_addons
cd /home/go/apps/develop/odoo/dev-mtg/custom_addons

# Verificar que Git esté inicializado
git status

# Deberías ver algo como:
# On branch dev-mtg
# Your branch is up to date with 'origin/dev-mtg'.
```

---

## 🔄 Flujo de Trabajo Después de Conectar

Una vez conectado, puedes usar Git normalmente:

### Desde la Terminal del Servidor

```bash
cd /home/go/apps/develop/odoo/dev-mtg/custom_addons

# Ver cambios
git status

# Agregar archivos
git add .

# Hacer commit
git commit -m "Descripción de cambios"

# Subir a GitHub
git push origin dev-mtg
```

### Desde la API (próximamente en UI)

También puedes usar los endpoints de la API para hacer commits y push:

```bash
# Ver estado
curl -X GET https://api-dev.hospitalprivadosalta.ar/api/github/status/dev-mtg \
  -H "Authorization: Bearer TU_JWT_TOKEN"

# Hacer commit
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/commit \
  -H "Authorization: Bearer TU_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "dev-mtg",
    "message": "Actualización de módulos"
  }'

# Push a GitHub
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/github/push \
  -H "Authorization: Bearer TU_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instance_name": "dev-mtg"}'
```

---

## 🎨 Características de la UI

### Botón GitHub

- **Ubicación**: En cada instancia de desarrollo
- **Estilo**: Botón con borde, ícono de GitHub
- **Función**: Abre el modal de configuración

### Modal de Configuración

- **Campos**:
  - Token de GitHub (campo de contraseña)
  - URL del Repositorio
- **Validaciones**:
  - Verifica que el token sea válido
  - Valida el formato de la URL
  - Verifica que la carpeta local exista
- **Estados**:
  - Input: Formulario inicial
  - Verifying: Verificando token
  - Configuring: Configurando repositorio
  - Success: Conexión exitosa
  - Error: Muestra errores si algo falla
  - Configured: Si ya está conectado

### Notificaciones

- **Toast de éxito**: Cuando la conexión se completa
- **Mensajes de error**: Si algo falla en el proceso
- **Indicadores de carga**: Durante el proceso de conexión

---

## 🔍 Verificación de Configuración Existente

Si ya has conectado GitHub anteriormente:

1. Al hacer clic en el botón **"GitHub"**
2. El modal detectará automáticamente la configuración existente
3. Mostrará un mensaje verde indicando que ya está conectado
4. Mostrará el repositorio y rama configurados

---

## 🐛 Solución de Problemas

### Error: "Token de GitHub inválido"

- Verifica que el token sea correcto
- Asegúrate de que tenga permisos `repo`
- Genera un nuevo token si es necesario

### Error: "URL de repositorio inválida"

- Usa el formato: `https://github.com/usuario/repositorio`
- No incluyas `.git` al final
- Verifica que el repositorio exista

### Error: "La ruta no existe"

- Verifica que la instancia `dev-mtg` esté creada
- Confirma que la carpeta `custom_addons` exista
- Ruta esperada: `/home/go/apps/develop/odoo/dev-mtg/custom_addons`

### El modal no se abre

- Verifica que estés viendo una instancia de **desarrollo**
- El botón GitHub solo aparece en instancias dev, no en producción
- Recarga la página si es necesario

---

## 📝 Archivos Modificados

### Frontend

1. **`/home/go/api/frontend/src/lib/api.js`**
   - Agregados endpoints de GitHub

2. **`/home/go/api/frontend/src/components/GitHubModal.jsx`** (NUEVO)
   - Modal de configuración de GitHub
   - Flujo automático de conexión

3. **`/home/go/api/frontend/src/components/Instances.jsx`**
   - Agregado botón GitHub en instancias dev
   - Integración con GitHubModal

### Backend

- Ya existían todos los endpoints necesarios en `/home/go/api/backend/routes/github.py`

---

## 🚀 Próximos Pasos Sugeridos

1. **Agregar botones de Git en la UI**:
   - Botón "Commit" para hacer commits desde la interfaz
   - Botón "Push" para subir cambios
   - Botón "Pull" para bajar cambios
   - Ver historial de commits

2. **Panel de Git**:
   - Ver archivos modificados
   - Diff de cambios
   - Historial de commits con detalles

3. **Notificaciones**:
   - Alertas cuando hay cambios sin commitear
   - Notificaciones de push/pull exitosos

---

## ✨ Ventajas de Esta Implementación

- ✅ **Un solo clic**: Todo el proceso automatizado
- ✅ **Sin terminal**: No necesitas SSH para conectar
- ✅ **Validación automática**: Verifica token y configuración
- ✅ **Rama automática**: Crea la rama con el nombre de la instancia
- ✅ **Ruta automática**: Usa la ruta correcta de custom_addons
- ✅ **Feedback visual**: Estados claros del proceso
- ✅ **Detección de configuración**: Sabe si ya está conectado

---

**¡Listo para probar!** 🎉

Simplemente accede al panel web, busca tu instancia `dev-mtg` y haz clic en el botón GitHub.
