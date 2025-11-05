ahor# 🔐 Configuración SSL - Guía Completa

## Descripción General

Los scripts de creación de instancias Odoo ahora soportan **múltiples métodos de certificados SSL**:

1. **Let's Encrypt (Certbot)** - Automático, gratis, renovación cada 90 días
2. **Cloudflare Origin Certificate** - Manual, gratis, válido 15 años
3. **Solo HTTP** - Sin SSL (no recomendado para producción)

## Selección Interactiva

Al ejecutar cualquier script de inicialización de producción, **al inicio del proceso** (antes de crear la instancia), se te preguntará:

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

Selecciona una opción (1-3):
```

## Opción 1: Let's Encrypt (Certbot)

### Ventajas
- ✅ Completamente automático
- ✅ Renovación automática cada 90 días
- ✅ Certificado confiable por todos los navegadores
- ✅ No requiere configuración manual

### Desventajas
- ⚠️ Límite de 5 certificados por dominio exacto cada 7 días
- ⚠️ Requiere que el dominio apunte directamente a tu servidor
- ⚠️ Necesita puerto 80 abierto para validación

### Cuándo Usar
- Primera instalación de producción
- Dominios que apuntan directamente al servidor (sin Cloudflare proxy)
- Cuando no has alcanzado el límite de tasa

### Proceso Automático
1. Script crea configuración HTTP temporal en Nginx
2. Certbot valida el dominio vía HTTP
3. Obtiene certificado SSL
4. Configura Nginx con HTTPS automáticamente
5. Agrega redirección HTTP → HTTPS

### Verificar Certificados Existentes
```bash
# Ver todos los certificados
sudo certbot certificates

# Ver fecha de expiración
sudo openssl x509 -enddate -noout -in /etc/letsencrypt/live/DOMINIO/fullchain.pem

# Renovar manualmente
sudo certbot renew

# Renovar forzadamente (cuenta para límite de tasa)
sudo certbot renew --force-renewal
```

### Solución de Problemas

#### Error: Límite de Tasa Alcanzado
```
too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s
```

**Solución:**
- Espera hasta la fecha indicada en el error
- O usa Opción 2 (Cloudflare)
- O usa Opción 3 (HTTP temporal)

#### Error: Validación Fallida
```bash
# Verificar DNS
dig DOMINIO

# Verificar puerto 80
sudo lsof -i :80

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx
```

## Opción 2: Cloudflare Origin Certificate

### Ventajas
- ✅ Sin límites de tasa
- ✅ Válido por 15 años
- ✅ Ideal para dominios en Cloudflare
- ✅ No requiere renovación frecuente

### Desventajas
- ⚠️ Requiere configuración manual inicial
- ⚠️ Solo funciona con Cloudflare como proxy
- ⚠️ Certificado no es confiable directamente (solo entre Cloudflare y tu servidor)

### Cuándo Usar
- Dominio usa Cloudflare como proxy
- Has alcanzado límite de Let's Encrypt
- Quieres evitar renovaciones frecuentes
- Instalaciones de producción estables

### Proceso de Configuración

#### Paso 1: Crear Certificado en Cloudflare

1. Ve a [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Selecciona tu dominio
3. Ve a **SSL/TLS** > **Origin Server**
4. Click en **Create Certificate**
5. Configuración:
   - **Private key type:** RSA (2048)
   - **Certificate Validity:** 15 years
   - **Hostnames:** 
     - `grupoorange.ar`
     - `*.grupoorange.ar` (si quieres wildcard)
6. Click **Create**
7. **IMPORTANTE:** Copia ambos:
   - Origin Certificate (todo el texto)
   - Private Key (todo el texto)

#### Paso 2: Instalar en el Servidor

El script creará archivos temporales que debes reemplazar:

```bash
# Editar certificado
sudo nano /etc/ssl/cloudflare/grupoorange.ar.crt
# Pega el Origin Certificate completo (incluye BEGIN y END)

# Editar clave privada
sudo nano /etc/ssl/cloudflare/grupoorange.ar.key
# Pega la Private Key completa (incluye BEGIN y END)

# Ajustar permisos
sudo chmod 644 /etc/ssl/cloudflare/grupoorange.ar.crt
sudo chmod 600 /etc/ssl/cloudflare/grupoorange.ar.key

# Verificar sintaxis de Nginx
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

#### Paso 3: Configurar Cloudflare SSL Mode

1. En Cloudflare Dashboard
2. SSL/TLS > Overview
3. Selecciona **Full (strict)**

**Modos SSL de Cloudflare:**

- **Off:** Sin SSL (no usar)
- **Flexible:** HTTPS entre usuario y Cloudflare, HTTP entre Cloudflare y servidor (menos seguro)
- **Full:** HTTPS end-to-end, acepta certificados autofirmados
- **Full (strict):** HTTPS end-to-end, requiere certificado válido (recomendado con Origin Certificate)

### Verificación

```bash
# Verificar certificado instalado
sudo openssl x509 -in /etc/ssl/cloudflare/grupoorange.ar.crt -text -noout

# Ver fecha de expiración
sudo openssl x509 -enddate -noout -in /etc/ssl/cloudflare/grupoorange.ar.crt

# Verificar que Nginx use el certificado
sudo nginx -T | grep ssl_certificate

# Test desde el servidor
curl -I https://grupoorange.ar

# Test desde fuera (con Cloudflare)
curl -I https://grupoorange.ar -H "Host: grupoorange.ar"
```

## Opción 3: Solo HTTP

### Cuándo Usar
- Desarrollo local
- Testing temporal
- Mientras esperas que expire límite de Let's Encrypt
- Detrás de proxy que maneja SSL

### Configuración
El script configura Nginx solo en puerto 80, sin redirección a HTTPS.

### Agregar SSL Después

```bash
# Opción 1: Certbot
sudo certbot --nginx -d grupoorange.ar --redirect

# Opción 2: Configurar manualmente con Cloudflare
# Sigue los pasos de Opción 2
```

## Comparación de Métodos

| Característica | Let's Encrypt | Cloudflare Origin | Solo HTTP |
|----------------|---------------|-------------------|-----------|
| Costo | Gratis | Gratis | Gratis |
| Configuración | Automática | Manual inicial | Automática |
| Validez | 90 días | 15 años | N/A |
| Renovación | Automática | No necesaria | N/A |
| Límites | 5/semana | Sin límites | N/A |
| Requiere Cloudflare | No | Sí | No |
| Confianza navegadores | Sí | Solo con CF proxy | No (HTTP) |
| Recomendado para | Dominios directos | Dominios en CF | Testing |

## Arquitectura de Archivos

### Let's Encrypt
```
/etc/letsencrypt/
├── live/
│   └── grupoorange.ar/
│       ├── fullchain.pem
│       ├── privkey.pem
│       ├── cert.pem
│       └── chain.pem
├── renewal/
│   └── grupoorange.ar.conf
└── options-ssl-nginx.conf
```

### Cloudflare Origin
```
/etc/ssl/cloudflare/
├── grupoorange.ar.crt
└── grupoorange.ar.key
```

### Nginx
```
/etc/nginx/
├── sites-available/
│   └── odoo-production
└── sites-enabled/
    └── odoo-production -> ../sites-available/odoo-production
```

## Scripts Afectados

Los siguientes scripts ahora incluyen selección interactiva de SSL:

- `scripts/odoo/init-production-18e.sh` - Odoo 18 Enterprise
- `scripts/odoo/init-production-19e.sh` - Odoo 19 Enterprise
- `scripts/odoo/init-production-19c.sh` - Odoo 19 Community

## Módulo SSL Manager

El módulo `scripts/utils/ssl-manager.sh` proporciona:

### Funciones Principales

```bash
# Mostrar menú de selección
prompt_ssl_method()

# Configurar SSL según método elegido
configure_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$SSL_METHOD"

# Configurar Let's Encrypt
setup_letsencrypt_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT"

# Configurar Cloudflare Origin
setup_cloudflare_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT"

# Configurar solo HTTP
configure_http_only "$DOMAIN" "$INSTANCE_NAME" "$PORT"
```

### Uso Programático

```bash
# Cargar módulo
source /home/go/api-dev/scripts/utils/ssl-manager.sh

# Usar directamente (sin prompt)
configure_ssl "grupoorange.ar" "production" "8069" "1"  # Let's Encrypt
configure_ssl "grupoorange.ar" "production" "8069" "2"  # Cloudflare
configure_ssl "grupoorange.ar" "production" "8069" "3"  # Solo HTTP
```

## Mejores Prácticas

### Para Producción
1. ✅ Usa **Cloudflare Origin Certificate** si tu dominio está en Cloudflare
2. ✅ Usa **Let's Encrypt** si el dominio apunta directamente al servidor
3. ✅ Configura **Full (strict)** en Cloudflare
4. ✅ Monitorea expiración de certificados
5. ✅ Incluye `/etc/letsencrypt/` y `/etc/ssl/cloudflare/` en backups

### Para Desarrollo
1. ✅ Usa **Solo HTTP** para testing local
2. ✅ Usa **Let's Encrypt staging** para probar scripts
3. ✅ No uses certificados de producción en desarrollo

### Seguridad
1. 🔒 Nunca compartas claves privadas
2. 🔒 Permisos correctos: `chmod 600` para `.key`
3. 🔒 Usa **Full (strict)** en Cloudflare, no Flexible
4. 🔒 Mantén Nginx actualizado
5. 🔒 Revisa logs regularmente

## Troubleshooting

### Certificado No Funciona

```bash
# Verificar configuración Nginx
sudo nginx -t

# Ver qué certificado usa Nginx
sudo nginx -T | grep ssl_certificate

# Verificar permisos
ls -la /etc/letsencrypt/live/grupoorange.ar/
ls -la /etc/ssl/cloudflare/

# Verificar validez del certificado
sudo openssl x509 -in /etc/ssl/cloudflare/grupoorange.ar.crt -text -noout
```

### Renovación Falla

```bash
# Ver logs de Certbot
sudo tail -100 /var/log/letsencrypt/letsencrypt.log

# Probar renovación manualmente
sudo certbot renew --dry-run

# Verificar timer de renovación
sudo systemctl status certbot.timer
```

### Cloudflare Muestra Error 525

**Error 525: SSL Handshake Failed**

Causas:
- Certificado no instalado correctamente
- Permisos incorrectos
- Nginx no reiniciado
- SSL mode incorrecto en Cloudflare

Solución:
```bash
# Verificar certificado
sudo openssl x509 -in /etc/ssl/cloudflare/grupoorange.ar.crt -noout

# Verificar Nginx
sudo nginx -t
sudo systemctl restart nginx

# En Cloudflare: cambiar a Full (strict)
```

## Recursos Adicionales

- [Let's Encrypt Rate Limits](https://letsencrypt.org/docs/rate-limits/)
- [Cloudflare Origin CA](https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)

---

**Última actualización:** 2025-11-05
