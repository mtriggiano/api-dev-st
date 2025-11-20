# Changelog - Sistema SSL Flexible

## 2025-11-05 - Versión 2.0

### ✅ Correcciones Implementadas

#### 1. Pregunta SSL Movida al Inicio
**Problema:** La pregunta de método SSL se hacía después de crear toda la instancia Odoo.
**Solución:** Ahora se pregunta **al inicio del script**, antes de cualquier creación.

**Flujo anterior:**
```
1. Crear BD
2. Instalar Odoo
3. Configurar servicio
4. Iniciar Odoo
5. ❌ Preguntar SSL (muy tarde)
```

**Flujo nuevo:**
```
1. ✅ Preguntar SSL (al inicio)
2. Crear BD
3. Instalar Odoo
4. Configurar servicio
5. Iniciar Odoo
6. Aplicar configuración SSL elegida
```

#### 2. Captura de Entrada Corregida
**Problema:** La función `prompt_ssl_method()` no capturaba correctamente la entrada del usuario cuando se ejecutaba en un subshell `$()`.

**Solución:** 
- Usar `</dev/tty` para leer directamente del terminal
- Redirigir mensajes a `>&2` (stderr) para que no interfieran con el valor de retorno
- Solo el número elegido se envía a stdout

**Código anterior:**
```bash
read -p "Selecciona una opción (1-3): " SSL_CHOICE
```

**Código nuevo:**
```bash
read -p "Selecciona una opción (1-3): " SSL_CHOICE </dev/tty
echo "mensaje" >&2  # Mensajes a stderr
echo "$SSL_CHOICE"  # Solo el valor a stdout
```

#### 3. Información Antes de Preguntar
**Problema:** El script pedía el número sin mostrar primero las opciones.

**Solución:** El menú completo se muestra antes de pedir input:
```
🔐 ============================================
   SELECCIONA MÉTODO DE CERTIFICADO SSL
============================================

1) Let's Encrypt (Certbot) - Gratis, automático
   ✅ Renovación automática cada 90 días
   ⚠️  Límite: 5 certificados por dominio/semana

2) Cloudflare Origin Certificate - Gratis, 15 años
   ✅ Sin límites de tasa
   ✅ Válido por 15 años
   ⚠️  Requiere configuración manual inicial

3) Solo HTTP (sin SSL)
   ⚠️  No recomendado para producción

Selecciona una opción (1-3): _
```

### 📝 Archivos Modificados

#### Scripts de Producción
- `scripts/odoo/init-production-18e.sh`
- `scripts/odoo/init-production-19e.sh`
- `scripts/odoo/init-production-19c.sh`

**Cambios:**
1. Agregada llamada a `prompt_ssl_method()` al inicio
2. Variable `SSL_METHOD` capturada antes de crear instancia
3. Eliminada segunda llamada redundante después de iniciar Odoo

#### Módulo SSL Manager
- `scripts/utils/ssl-manager.sh`

**Cambios:**
1. Función `prompt_ssl_method()` corregida para captura correcta
2. Uso de `</dev/tty` para input
3. Uso de `>&2` para mensajes informativos

#### Documentación
- `docs/SSL_CONFIGURATION.md` - Actualizada para indicar que pregunta es al inicio
- `README.md` - Ya incluye la nueva funcionalidad

### 🧪 Testing

Creado script de prueba:
```bash
./scripts/utils/test-ssl-prompt.sh
```

Este script permite probar la función `prompt_ssl_method()` de forma aislada.

### 🎯 Resultado Final

**Experiencia de Usuario:**
1. Usuario ejecuta: `./scripts/odoo/init-production-19e.sh production`
2. Script muestra menú SSL inmediatamente
3. Usuario selecciona opción (1, 2 o 3)
4. Script confirma selección
5. Script procede a crear instancia
6. Al final, aplica configuración SSL elegida

**Ventajas:**
- ✅ Usuario sabe desde el inicio qué método SSL se usará
- ✅ No pierde tiempo si elige opción incorrecta
- ✅ Puede cancelar antes de crear la instancia
- ✅ Flujo más lógico y predecible

### 🔄 Compatibilidad

Los cambios son **100% compatibles** con:
- Scripts existentes que usan el módulo SSL
- Variables de entorno en `.env`
- Configuraciones de Nginx existentes
- Certificados SSL ya instalados

### 📚 Documentación Relacionada

- [SSL_CONFIGURATION.md](docs/SSL_CONFIGURATION.md) - Guía completa de SSL
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Solución de problemas SSL
- [README.md](README.md) - Características generales

---

**Fecha:** 2025-11-05  
**Versión:** 2.0  
**Estado:** ✅ Completado y Probado
