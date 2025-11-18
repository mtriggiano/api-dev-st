#!/bin/bash

# 🚀 Script de despliegue del Server Panel - Versión refactorizada
# Despliega el backend Flask y el frontend React

set -e

# Cargar variables de entorno
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_ROOT/scripts/utils/load-env.sh"

# Validar variables requeridas
source "$PROJECT_ROOT/scripts/utils/validate-env.sh" \
    API_DOMAIN CF_API_TOKEN DOMAIN_ROOT PUBLIC_IP \
    DB_USER DB_PASSWORD SECRET_KEY JWT_SECRET_KEY

DOMAIN="${API_DOMAIN}"
API_DIR="${PROJECT_ROOT:-/home/mtg/api-dev}"
BACKEND_DIR="$API_DIR/backend"
FRONTEND_DIR="$API_DIR/frontend"
USER="${SYSTEM_USER:-go}"
PUBLIC_IP="${PUBLIC_IP}"
CF_API_TOKEN="${CF_API_TOKEN}"
CF_ZONE_NAME="${DOMAIN_ROOT}"

echo "🚀 Iniciando despliegue del Server Panel..."

# Verificar que estamos en el directorio correcto
cd "$API_DIR"

# 1. Configurar DNS en Cloudflare
echo "🌐 Configurando DNS en Cloudflare..."
CF_ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$CF_ZONE_NAME" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.result[0].id')

curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"type":"A","name":"'"$DOMAIN"'","content":"'"$PUBLIC_IP"'","ttl":3600,"proxied":false}' >/dev/null

echo "✅ DNS configurado"

# Esperar propagación DNS antes de solicitar el certificado SSL
echo "⏳ Verificando propagación DNS..."
MAX_WAIT=600  # 10 minutos
SLEEP_INTERVAL=15
ELAPSED=0
DNS_READY=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    RESOLVED_IP=$(dig +short "$DOMAIN" A @1.1.1.1 | tail -n 1)

    if [ -n "$RESOLVED_IP" ] && [ "$RESOLVED_IP" = "$PUBLIC_IP" ]; then
        echo "✅ DNS propagado correctamente ($RESOLVED_IP)"
        DNS_READY=1
        break
    fi

    CURRENT_DISPLAY=${RESOLVED_IP:-sin registro}
    echo "⏳ DNS aún no apunta a $PUBLIC_IP (actual: $CURRENT_DISPLAY). Reintentando en ${SLEEP_INTERVAL}s..."
    sleep $SLEEP_INTERVAL
    ELAPSED=$((ELAPSED + SLEEP_INTERVAL))
done

if [ $DNS_READY -ne 1 ]; then
    echo "⚠️ Advertencia: el DNS aún no apunta a $PUBLIC_IP después de $MAX_WAIT segundos."
    echo "   Se omitirá la solicitud automática del certificado SSL."
fi

# 2. Verificar dependencias del sistema
echo "📦 Verificando dependencias del sistema..."

# Dependencias críticas
MISSING_DEPS=""
for cmd in python3.12 node npm nginx psql pg_dump git jq certbot; do
    if ! command -v $cmd >/dev/null 2>&1; then
        echo "❌ $cmd no está instalado"
        MISSING_DEPS="$MISSING_DEPS $cmd"
    else
        echo "✅ $cmd encontrado"
    fi
done

if [ -n "$MISSING_DEPS" ]; then
    echo ""
    echo "❌ Dependencias faltantes:$MISSING_DEPS"
    echo ""
    echo "Para instalarlas en Ubuntu/Debian:"
    echo "sudo apt update"
    echo "sudo apt install -y python3.12 nodejs npm nginx postgresql-client git jq certbot python3-certbot-nginx"
    echo ""
    read -p "¿Deseas continuar de todos modos? (s/n): " CONTINUE
    if [ "$CONTINUE" != "s" ] && [ "$CONTINUE" != "S" ]; then
        exit 1
    fi
fi

# Verificar PostgreSQL
echo "🗄️ Verificando PostgreSQL..."
if sudo systemctl status postgresql >/dev/null 2>&1; then
    echo "✅ PostgreSQL está corriendo"
else
    echo "⚠️ PostgreSQL no está corriendo"
    echo "Intentando iniciar PostgreSQL..."
    sudo systemctl start postgresql || {
        echo "❌ No se pudo iniciar PostgreSQL"
        exit 1
    }
fi

# 3. Configurar backend
echo "🐍 Configurando backend..."
cd "$BACKEND_DIR"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
  python3.12 -m venv venv
fi

# Activar y actualizar dependencias
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
  echo "📝 Creando archivo .env..."
  cp .env.example .env
  
  # Generar secrets aleatorios
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  
  sed -i "s/your-secret-key-change-this/$SECRET_KEY/" .env
  sed -i "s/your-jwt-secret-key-change-this/$JWT_SECRET_KEY/" .env
fi

# Crear base de datos PostgreSQL
echo "🗄️ Configurando base de datos..."
DB_NAME="${DB_NAME_PANEL:-server_panel}"
DB_USER="${DB_USER:-go}"

# Verificar/crear usuario PostgreSQL
echo "👤 Verificando usuario PostgreSQL '$DB_USER'..."
if sudo -u postgres psql -c "\du" | grep -q "$DB_USER"; then
  echo "✅ Usuario PostgreSQL existe"
else
  echo "📦 Creando usuario PostgreSQL '$DB_USER'..."
  sudo -u postgres createuser -s "$DB_USER" || {
    echo "❌ No se pudo crear el usuario PostgreSQL"
    exit 1
  }
  # Establecer contraseña si está configurada
  if [ -n "$DB_PASSWORD" ]; then
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
  fi
  echo "✅ Usuario PostgreSQL creado"
fi

# Verificar si la BD ya existe
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
  echo "✅ Base de datos ya existe"
else
  echo "📦 Creando base de datos..."
  sudo -u postgres createdb "$DB_NAME" -O "$DB_USER" --encoding='UTF8' || {
    echo "❌ No se pudo crear la base de datos"
    exit 1
  }
  echo "✅ Base de datos creada"
fi

# Crear directorios necesarios
echo "📁 Creando estructura de directorios..."
mkdir -p "$API_DIR/logs"
mkdir -p "$API_DIR/data"
mkdir -p "${BACKUPS_PATH:-/home/mtg/backups}"
mkdir -p "${PROD_ROOT:-/home/mtg/apps/production/odoo}"
mkdir -p "${DEV_ROOT:-/home/mtg/apps/develop/odoo}"
touch "$API_DIR/data/puertos_ocupados_odoo.txt"
touch "$API_DIR/data/dev-instances.txt"
chmod 755 "$API_DIR/logs" "$API_DIR/data"
echo "✅ Directorios creados"

# Hacer scripts ejecutables
echo "🔧 Configurando permisos de scripts..."
if [ -d "$API_DIR/scripts/odoo" ]; then
    chmod +x "$API_DIR/scripts/odoo/"*.sh 2>/dev/null || true
    echo "✅ Scripts de Odoo configurados"
fi
if [ -d "$API_DIR/scripts/utils" ]; then
    chmod +x "$API_DIR/scripts/utils/"*.sh 2>/dev/null || true
    echo "✅ Scripts de utilidades configurados"
fi

# Inicializar base de datos
echo "🔧 Inicializando base de datos..."
python3 -c "from app import create_app, init_db; app = create_app(); init_db(app)"

# 4. Crear servicio systemd para el backend
echo "⚙️ Creando servicio systemd..."
sudo tee /etc/systemd/system/server-panel-api.service > /dev/null <<EOF
[Unit]
Description=Server Panel API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"

# Configuración de Gunicorn para archivos grandes y operaciones largas
# -w 4: 4 workers (ajustar según CPU)
# -b 127.0.0.1:5000: bind a localhost
# --timeout 600: timeout de 10 minutos para operaciones largas (backups)
# --max-requests 1000: reiniciar workers después de 1000 requests
# --max-requests-jitter 50: jitter para evitar reinicio simultáneo
# --limit-request-line 8190: límite de línea de request
# --limit-request-field_size 8190: límite de campo de header
ExecStart=$BACKEND_DIR/venv/bin/gunicorn \\
    -w 4 \\
    -b 127.0.0.1:5000 \\
    --timeout 600 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --limit-request-line 8190 \\
    --limit-request-field_size 8190 \\
    --access-logfile /home/$USER/api-dev/logs/gunicorn-access.log \\
    --error-logfile /home/$USER/api-dev/logs/gunicorn-error.log \\
    --log-level info \\
    wsgi:app

Restart=always
RestartSec=10

# Límites de recursos
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable server-panel-api
sudo systemctl restart server-panel-api

echo "✅ Servicio backend iniciado"

# 5. Construir frontend
echo "⚛️ Construyendo frontend..."
cd "$FRONTEND_DIR"

# Instalar dependencias
npm install

# Crear archivo .env para producción
echo "VITE_API_URL=https://$DOMAIN" > .env.production

# Build
npm run build

# Ajustar permisos para que Nginx pueda leer los archivos
chmod -R 755 "$FRONTEND_DIR/dist"
chmod 755 /home/$USER "$API_DIR" "$FRONTEND_DIR"

echo "✅ Frontend construido"

# 6. Configurar Nginx
echo "🌐 Configurando Nginx..."

# Crear configuración temporal HTTP para obtener certificado
sudo tee /etc/nginx/sites-available/server-panel > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Permitir archivos grandes (backups hasta 1GB)
    client_max_body_size 1024M;
    client_body_timeout 600s;
    client_header_timeout 600s;

    # Frontend (archivos estáticos)
    location / {
        root $FRONTEND_DIR/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # API Backend
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        
        # Timeouts para operaciones largas (backups, restauración)
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        
        # Buffering para archivos grandes
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
    }
}
EOF

# Habilitar sitio
sudo ln -sf /etc/nginx/sites-available/server-panel /etc/nginx/sites-enabled/server-panel

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx

# 7. Obtener certificado SSL
echo "🔐 Obteniendo certificado SSL..."
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  if [ $DNS_READY -eq 1 ]; then
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN --redirect
    echo "✅ Certificado SSL obtenido"
  else
    echo "⚠️ Certificado SSL omitido porque el DNS aún no propaga a $PUBLIC_IP."
    echo "   Una vez propagado, ejecuta manualmente:"
    echo "   sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN --redirect"
  fi
else
  echo "✅ Certificado SSL ya existe"
fi

# 8. Crear cron job para guardar métricas cada minuto
echo "⏰ Configurando cron job para métricas..."
CRON_JOB="* * * * * curl -X POST http://localhost:5000/api/metrics/save >/dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "/api/metrics/save"; echo "$CRON_JOB") | crontab -

echo ""
echo "✅ ¡Despliegue completado con éxito!"
echo ""
echo "📋 Información del despliegue:"
echo "   🌐 URL: https://$DOMAIN"
echo "   👤 Usuario: admin"
echo "   🔑 Contraseña: Pipoloko09 (cambiar después del primer login)"
echo ""
echo "📜 Comandos útiles:"
echo "   Ver logs del backend: sudo journalctl -u server-panel-api -f"
echo "   Reiniciar backend: sudo systemctl restart server-panel-api"
echo "   Estado del backend: sudo systemctl status server-panel-api"
echo "   Recargar Nginx: sudo systemctl reload nginx"
echo ""
