#!/bin/bash

# 🔐 SSL Manager - Gestión de certificados SSL
# Soporta Let's Encrypt (Certbot) y Cloudflare Origin Certificates

# Función para obtener certificado Origin de Cloudflare
setup_cloudflare_ssl() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    
    echo "☁️ Configurando SSL con Cloudflare Origin Certificate..."
    
    # Verificar variables de entorno
    if [[ -z "$CF_API_TOKEN" ]]; then
        echo "❌ Error: CF_API_TOKEN no está configurado en .env"
        return 1
    fi
    
    if [[ -z "$CF_ZONE_ID" ]]; then
        echo "❌ Error: CF_ZONE_ID no está configurado en .env"
        return 1
    fi
    
    # Directorio para certificados de Cloudflare
    CF_CERT_DIR="/etc/ssl/cloudflare"
    sudo mkdir -p "$CF_CERT_DIR"
    
    CERT_FILE="$CF_CERT_DIR/$DOMAIN.crt"
    KEY_FILE="$CF_CERT_DIR/$DOMAIN.key"
    
    # Verificar si ya existe un certificado válido
    if [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]]; then
        if sudo openssl x509 -checkend 2592000 -noout -in "$CERT_FILE" 2>/dev/null; then
            echo "✅ Certificado Cloudflare válido encontrado (expira en más de 30 días)"
            configure_nginx_cloudflare_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$CERT_FILE" "$KEY_FILE"
            return 0
        else
            echo "⚠️  Certificado encontrado pero expira pronto"
        fi
    fi
    
    echo "📜 Solicitando certificado Origin de Cloudflare..."
    echo ""
    echo "⚠️  IMPORTANTE: Debes crear el certificado manualmente en Cloudflare:"
    echo "   1. Ve a: https://dash.cloudflare.com"
    echo "   2. Selecciona tu dominio"
    echo "   3. SSL/TLS > Origin Server"
    echo "   4. Create Certificate"
    echo "   5. Hostnames: $DOMAIN"
    echo "   6. Validity: 15 years"
    echo "   7. Copia el certificado y la clave privada"
    echo ""
    echo "📋 Pegando certificado y clave..."
    
    # Crear certificado temporal (el usuario debe reemplazarlo)
    echo "# REEMPLAZAR CON CERTIFICADO DE CLOUDFLARE" | sudo tee "$CERT_FILE" > /dev/null
    echo "# REEMPLAZAR CON CLAVE PRIVADA DE CLOUDFLARE" | sudo tee "$KEY_FILE" > /dev/null
    
    sudo chmod 644 "$CERT_FILE"
    sudo chmod 600 "$KEY_FILE"
    
    echo ""
    echo "📝 Para completar la configuración, ejecuta:"
    echo "   sudo nano $CERT_FILE"
    echo "   sudo nano $KEY_FILE"
    echo ""
    echo "   Luego recarga Nginx:"
    echo "   sudo nginx -t && sudo systemctl reload nginx"
    echo ""
    
    # Configurar Nginx con SSL (aunque el cert sea temporal)
    configure_nginx_cloudflare_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$CERT_FILE" "$KEY_FILE"
    
    return 0
}

# Función para configurar Nginx con certificado de Cloudflare
configure_nginx_cloudflare_ssl() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    local CERT_FILE=$4
    local KEY_FILE=$5
    
    echo "🔧 Configurando Nginx con SSL de Cloudflare..."
    
    # Crear configuración Nginx con SSL
    sudo tee /etc/nginx/sites-available/$INSTANCE_NAME > /dev/null <<EOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # Certificado Origin de Cloudflare
    ssl_certificate $CERT_FILE;
    ssl_certificate_key $KEY_FILE;
    
    # Configuración SSL optimizada
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 20M;

    # Bloquear acceso al gestor de bases de datos
    location ~* ^/web/database/(manager|selector|create|duplicate|drop|backup|restore|change_password) {
        deny all;
        return 403;
    }

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_http_version 1.1;
        proxy_read_timeout 720s;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/$INSTANCE_NAME /etc/nginx/sites-enabled/$INSTANCE_NAME
    
    echo "✅ Configuración Nginx creada"
}

# Función para configurar SSL con Let's Encrypt (Certbot)
setup_letsencrypt_ssl() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    
    echo "🔐 Configurando SSL con Let's Encrypt (Certbot)..."
    
    # Verificar si el certificado existe y es válido
    SSL_CERT_EXISTS=false
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        if sudo openssl x509 -checkend 86400 -noout -in "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" 2>/dev/null; then
            SSL_CERT_EXISTS=true
            echo "✅ Certificado Let's Encrypt válido encontrado para $DOMAIN"
        else
            echo "⚠️  Certificado encontrado pero expira pronto o es inválido"
        fi
    fi
    
    if [ "$SSL_CERT_EXISTS" = false ]; then
        echo "🚫 Certificado no encontrado. Creando configuración HTTP temporal..."
        
        # Crear configuración HTTP temporal
        sudo tee /etc/nginx/sites-available/$INSTANCE_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 20M;

    # Bloquear acceso al gestor de bases de datos
    location ~* ^/web/database/(manager|selector|create|duplicate|drop|backup|restore|change_password) {
        deny all;
        return 403;
    }

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_read_timeout 720s;
    }
}
EOF
        
        sudo ln -sf /etc/nginx/sites-available/$INSTANCE_NAME /etc/nginx/sites-enabled/$INSTANCE_NAME
        
        echo "🔄 Recargando Nginx con configuración HTTP..."
        sudo nginx -t && sudo systemctl reload nginx || sudo systemctl start nginx
        
        echo "📜 Obteniendo certificado SSL con Certbot..."
        echo "⚠️  NOTA: Si alcanzaste el límite de tasa de Let's Encrypt (5 certs/semana),"
        echo "   espera hasta que expire el límite o usa Cloudflare SSL."
        
        if sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN --redirect; then
            echo "✅ Certificado SSL obtenido y configurado automáticamente por Certbot"
            return 0
        else
            echo "❌ Error al obtener certificado SSL."
            echo "   El sitio quedará configurado con HTTP en el puerto 80."
            echo "   Para obtener SSL manualmente más tarde, ejecuta:"
            echo "   sudo certbot --nginx -d $DOMAIN"
            return 1
        fi
    else
        echo "✅ Reutilizando certificado existente..."
        configure_nginx_letsencrypt_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT"
        return 0
    fi
}

# Función para configurar Nginx con certificado de Let's Encrypt existente
configure_nginx_letsencrypt_ssl() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    
    echo "🔧 Configurando Nginx con SSL de Let's Encrypt..."
    
    sudo tee /etc/nginx/sites-available/$INSTANCE_NAME > /dev/null <<EOF
map \$http_upgrade \$connection_upgrade {
    default upgrade;
    '' close;
}

server {
    server_name $DOMAIN;

    client_max_body_size 20M;

    # Bloquear acceso al gestor de bases de datos
    location ~* ^/web/database/(manager|selector|create|duplicate|drop|backup|restore|change_password) {
        deny all;
        return 403;
    }

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \$connection_upgrade;
        proxy_http_version 1.1;
        proxy_read_timeout 720s;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if (\$host = $DOMAIN) {
        return 301 https://\$host\$request_uri;
    }

    listen 80;
    server_name $DOMAIN;
    return 404;
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/$INSTANCE_NAME /etc/nginx/sites-enabled/$INSTANCE_NAME
    
    echo "🔄 Recargando Nginx con configuración HTTPS..."
    sudo nginx -t && sudo systemctl reload nginx
    
    echo "✅ Configuración Nginx creada con SSL"
}

# Función principal para configurar SSL
configure_ssl() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    local SSL_METHOD=$4
    
    echo ""
    echo "🔐 ============================================"
    echo "   CONFIGURACIÓN SSL"
    echo "============================================"
    echo ""
    
    # Eliminar configuración anterior si existe
    [[ -L "/etc/nginx/sites-enabled/$INSTANCE_NAME" ]] && sudo rm -f "/etc/nginx/sites-enabled/$INSTANCE_NAME"
    
    case $SSL_METHOD in
        1|certbot|letsencrypt)
            setup_letsencrypt_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT"
            ;;
        2|cloudflare|cf)
            setup_cloudflare_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT"
            ;;
        3|none|skip)
            echo "⚠️  Omitiendo configuración SSL. Configurando solo HTTP..."
            configure_http_only "$DOMAIN" "$INSTANCE_NAME" "$PORT"
            ;;
        *)
            echo "❌ Método SSL no válido: $SSL_METHOD"
            return 1
            ;;
    esac
    
    echo ""
    echo "✅ Nginx configurado correctamente para $DOMAIN"
    echo ""
}

# Función para configurar solo HTTP (sin SSL)
configure_http_only() {
    local DOMAIN=$1
    local INSTANCE_NAME=$2
    local PORT=$3
    
    echo "🌐 Configurando Nginx solo con HTTP..."
    
    sudo tee /etc/nginx/sites-available/$INSTANCE_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 20M;

    # Bloquear acceso al gestor de bases de datos
    location ~* ^/web/database/(manager|selector|create|duplicate|drop|backup|restore|change_password) {
        deny all;
        return 403;
    }

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_read_timeout 720s;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/$INSTANCE_NAME /etc/nginx/sites-enabled/$INSTANCE_NAME
    
    echo "🔄 Recargando Nginx..."
    sudo nginx -t && sudo systemctl reload nginx
    
    echo "✅ Configuración HTTP creada"
}

# Función para mostrar menú de selección de SSL
prompt_ssl_method() {
    echo "" >&2
    echo "🔐 ============================================" >&2
    echo "   SELECCIONA MÉTODO DE CERTIFICADO SSL" >&2
    echo "============================================" >&2
    echo "" >&2
    echo "1) Let's Encrypt (Certbot) - Gratis, automático" >&2
    echo "   ✅ Renovación automática cada 90 días" >&2
    echo "   ⚠️  Límite: 5 certificados por dominio/semana" >&2
    echo "" >&2
    echo "2) Cloudflare Origin Certificate - Gratis, 15 años" >&2
    echo "   ✅ Sin límites de tasa" >&2
    echo "   ✅ Válido por 15 años" >&2
    echo "   ⚠️  Requiere configuración manual inicial" >&2
    echo "" >&2
    echo "3) Solo HTTP (sin SSL)" >&2
    echo "   ⚠️  No recomendado para producción" >&2
    echo "" >&2
    
    while true; do
        read -p "Selecciona una opción (1-3): " SSL_CHOICE </dev/tty
        case $SSL_CHOICE in
            1|2|3)
                echo "$SSL_CHOICE"
                return 0
                ;;
            *)
                echo "❌ Opción inválida. Por favor selecciona 1, 2 o 3." >&2
                ;;
        esac
    done
}
