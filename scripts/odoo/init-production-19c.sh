#!/bin/bash

# 🚀 Script de creación de instancia Odoo 19 Community - Versión refactorizada
# Usa variables de entorno desde archivo .env


# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"
source "$SCRIPT_DIR/../utils/ssl-manager.sh"
source "$SCRIPT_DIR/../utils/odoo-version-manager.sh"

# Validar variables requeridas
source "$SCRIPT_DIR/../utils/validate-env.sh" \
    CF_API_TOKEN CF_ZONE_NAME DB_USER DB_PASSWORD \
    ODOO_ADMIN_PASSWORD PUBLIC_IP PROD_ROOT

# Validaciones de comandos
command -v jq >/dev/null 2>&1 || { echo >&2 "❌ 'jq' no está instalado."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo >&2 "❌ 'curl' no está instalado."; exit 1; }
command -v git >/dev/null 2>&1 || { echo >&2 "❌ 'git' no está instalado."; exit 1; }

# Obtener configuración de versión desde odoo-versions.conf
REPO=$(get_repo_path "19" "community")
PYTHON=$(get_python_bin "19" "community")

if [[ -z "$REPO" ]] || [[ ! -f "$REPO" ]]; then
    echo "❌ ERROR: No se pudo obtener la ruta del repositorio Odoo 19 Community"
    echo "   Verifica que odoo-versions.conf esté configurado correctamente"
    list_odoo_versions
    exit 1
fi

# Variables desde .env (con valores por defecto para compatibilidad)
ODOO_ROOT="${PROD_ROOT:-/home/mtg/apps/production/odoo}"
PUERTOS_FILE="${PUERTOS_FILE:-$DATA_PATH/puertos_ocupados_odoo.txt}"
USER="${SYSTEM_USER:-go}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
ADMIN_PASSWORD="${ODOO_ADMIN_PASSWORD}"
CF_API_TOKEN="${CF_API_TOKEN}"
CF_ZONE_NAME="${DOMAIN_ROOT}"
CF_EMAIL="${CF_EMAIL:-admin@$CF_ZONE_NAME}"
PUBLIC_IP="${PUBLIC_IP}"

# 2. Instancia
RAW_NAME="$1"
SSL_METHOD_PARAM="$2"  # Opcional: 1=letsencrypt, 2=cloudflare, 3=http

if [[ -z "$RAW_NAME" ]]; then echo "❌ Debes pasar el nombre de la instancia."; exit 1; fi
INSTANCE=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')

# IMPORTANTE: Las instancias de producción SIEMPRE usan SUBDOMINIOS
# NUNCA se usa el dominio raíz para proteger el dominio principal
INSTANCE_NAME="prod-$INSTANCE"

# 🔧 Forzar salida en tiempo real al log y al frontend (correct placement)
LOG="/tmp/odoo-create-$INSTANCE_NAME.log"
exec > >(stdbuf -oL -eL tee -a "$LOG") 2>&1

USE_ROOT_DOMAIN=false
SUBDOMAIN="$INSTANCE.$CF_ZONE_NAME"

echo "ℹ️  Nota: Esta instancia usará el subdominio: $SUBDOMAIN"

LOG="/tmp/odoo-create-$INSTANCE_NAME.log"

echo "🚀 Iniciando creación de instancia Odoo: $INSTANCE_NAME"
echo "📝 Log: $LOG"
echo ""

# Determinar método SSL
if [[ -n "$SSL_METHOD_PARAM" ]]; then
    # Modo no-interactivo: usar parámetro
    SSL_METHOD="$SSL_METHOD_PARAM"
    echo "✅ Método SSL seleccionado: $SSL_METHOD"
else
    # Modo interactivo: preguntar
    SSL_METHOD=$(prompt_ssl_method)
    echo ""
    echo "✅ Método SSL seleccionado. Continuando con la creación..."
fi
echo ""

# Validar nombre
if [[ ! "$INSTANCE" =~ ^[a-z0-9_-]+$ ]]; then
  echo "❌ Nombre inválido. Solo letras, números, guiones y guiones bajos."
  exit 1
elif [[ -d "$ODOO_ROOT/$INSTANCE" ]]; then
  echo "⚠️  La instancia '$INSTANCE' ya existe. Abortando."
  exit 1
fi

# Cancelación segura
trap cleanup SIGINT
cleanup() {
  echo -e "\n❌ Instalación cancelada."
  [[ -d "$ODOO_ROOT/$INSTANCE_NAME" ]] && rm -rf "$ODOO_ROOT/$INSTANCE_NAME"
  sudo -u postgres dropdb "$INSTANCE_NAME" 2>/dev/null || true
  sed -i "/^$PORT$/d" "$PUERTOS_FILE" 2>/dev/null || true
  exit 1
}

# Verificar si ya existe un log para esta instancia
if [[ -f "$LOG" ]]; then
  echo "⚠️ Log previo encontrado, sobreescribiendo $LOG..."
  rm -f "$LOG"
fi

# 🔎 Buscar puerto libre
for port in $(seq 2000 3000); do
  if ! grep -q "^$port$" "$PUERTOS_FILE" 2>/dev/null && ! lsof -iTCP:$port -sTCP:LISTEN -t >/dev/null; then
    PORT=$port
    echo "$PORT" >> "$PUERTOS_FILE"
    break
  fi
done
[[ -z "$PORT" ]] && echo "❌ No se encontró un puerto libre. Abortando." && exit 1

# 🔎 Buscar EVENTED_PORT (gevent) libre para WebSocket/Longpolling
for eport in $(seq 8072 8999); do
  if ! grep -q "^$eport$" "$PUERTOS_FILE" 2>/dev/null && ! lsof -iTCP:$eport -sTCP:LISTEN -t >/dev/null; then
    EVENTED_PORT=$eport
    echo "$EVENTED_PORT" >> "$PUERTOS_FILE"
    break
  fi
done
[[ -z "$EVENTED_PORT" ]] && echo "❌ No se encontró un EVENTED_PORT libre. Abortando." && exit 1

# Configurar dominio según tipo de instancia
# IMPORTANTE: El dominio usa $INSTANCE (sin prefijo prod-) para subdominios limpios
if [[ "$USE_ROOT_DOMAIN" == true ]]; then
  DOMAIN="$CF_ZONE_NAME"
else
  DOMAIN="$INSTANCE.$CF_ZONE_NAME"  # Usa INSTANCE, no INSTANCE_NAME
fi
BASE_DIR="$ODOO_ROOT/$INSTANCE_NAME"
ODOO_LOG="$BASE_DIR/odoo.log"
ODOO_CONF="$BASE_DIR/odoo.conf"
SERVICE_FILE="/etc/systemd/system/odoo19c-$INSTANCE_NAME.service"
NGINX_CONF="/etc/nginx/sites-available/$INSTANCE_NAME"
INFO_FILE="$BASE_DIR/info-instancia.txt"
VENV_DIR="$BASE_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
APP_DIR="$BASE_DIR"

echo "🌐 Dominio: $DOMAIN"
echo "📁 Carpeta base: $BASE_DIR"
echo "🔌 Puerto: $PORT"
echo "🧲 Evented (gevent) port: $EVENTED_PORT"

# 4. DNS
echo "🌍 IP pública configurada: $PUBLIC_IP"
CF_ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$CF_ZONE_NAME" -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ -z "$CF_ZONE_ID" ] || [ "$CF_ZONE_ID" = "null" ]; then
  echo "❌ Error: No se pudo obtener el Zone ID de Cloudflare"
  exit 1
fi

echo "🌐 Configurando DNS en Cloudflare para $DOMAIN..."

# Verificar si el registro ya existe
EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$DOMAIN" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ ! -z "$EXISTING_RECORD" ] && [ "$EXISTING_RECORD" != "null" ]; then
  echo "⚠️  Registro DNS ya existe, actualizando..."
  curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$EXISTING_RECORD" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"type":"CNAME","name":"'"$DOMAIN"'","content":"offisla.ddns.net","ttl":3600,"proxied":true}' >/dev/null
  echo "✅ Registro DNS actualizado"
else
  DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"type":"CNAME","name":"'"$DOMAIN"'","content":"offisla.ddns.net","ttl":3600,"proxied":true}')
  
  if echo "$DNS_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    echo "✅ Registro DNS creado exitosamente"
  else
    echo "⚠️  Advertencia: Posible error al crear registro DNS"
    echo "   Respuesta: $(echo $DNS_RESPONSE | jq -r '.errors[0].message' 2>/dev/null || echo 'Sin detalles')"
  fi
fi

# Esperar un momento para que Cloudflare procese el cambio
echo "⏳ Esperando 5 segundos para que Cloudflare procese el cambio..."
sleep 5

# Verificar DNS con timeout reducido
echo "🛰️  Verificando propagación DNS..."
DNS_RESULT=$(dig +short "$DOMAIN" @1.1.1.1 2>/dev/null | head -1)

if [ ! -z "$DNS_RESULT" ]; then
  echo "✅ DNS resuelto a: $DNS_RESULT (Cloudflare)"
else
  echo "⚠️  DNS aún no visible, pero continuando (puede tomar unos minutos)..."
fi

# 5. Setup
echo "📁 Creando estructura de carpetas en $BASE_DIR..."
mkdir -p "$BASE_DIR"
cd "$BASE_DIR" || exit 1
echo "📁 Creando carpeta de instancia y custom_addons en $BASE_DIR..."
mkdir -p "$BASE_DIR"
mkdir -p "$BASE_DIR/custom_addons"
mkdir -p "$BASE_DIR/odoo-server"

# Enlazar addons personalizados globales si existen
GLOBAL_CUSTOM="/home/$USER/apps/custom_addons_global"
if [[ -d "$GLOBAL_CUSTOM" ]]; then
  ln -s "$GLOBAL_CUSTOM"/* "$BASE_DIR/custom_addons/" 2>/dev/null || true
fi

echo "📦 Descomprimiendo repositorio en $BASE_DIR/odoo-server..."
unzip "$REPO" -d "$BASE_DIR/tmp_unzip"

# Detectar si hay una subcarpeta o si los archivos están en la raíz
UNZIP_DIR="$BASE_DIR/tmp_unzip"
SUBDIR_COUNT=$(find "$UNZIP_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
FILE_COUNT=$(find "$UNZIP_DIR" -mindepth 1 -maxdepth 1 -type f | wc -l)

if [[ $SUBDIR_COUNT -eq 1 ]] && [[ $FILE_COUNT -eq 0 ]]; then
  # Hay exactamente una subcarpeta y ningún archivo en la raíz
  SUBDIR_NAME=$(ls -1 "$UNZIP_DIR")
  UNZIP_DIR="$UNZIP_DIR/$SUBDIR_NAME"
  echo "📁 Detectada subcarpeta en ZIP: $SUBDIR_NAME"
fi

cp "$UNZIP_DIR/setup.py" "$BASE_DIR/odoo-server/"
cp "$UNZIP_DIR/requirements.txt" "$BASE_DIR/odoo-server/requirements.txt"
cp -r "$UNZIP_DIR/odoo" "$BASE_DIR/odoo-server/"
cp -r "$UNZIP_DIR/addons" "$BASE_DIR/odoo-server/"
# Copiar odoo-bin y setup si existen
if [[ -f "$UNZIP_DIR/odoo-bin" ]]; then
  cp "$UNZIP_DIR/odoo-bin" "$BASE_DIR/odoo-server/"
  chmod +x "$BASE_DIR/odoo-server/odoo-bin"
fi
if [[ -d "$UNZIP_DIR/setup" ]]; then
  cp -r "$UNZIP_DIR/setup" "$BASE_DIR/odoo-server/"
fi
rm -rf "$BASE_DIR/tmp_unzip"

# Verificar que la carpeta odoo existe
if [[ ! -d "$BASE_DIR/odoo-server/odoo" ]]; then
  echo "❌ Error: Carpeta 'odoo' no encontrada en el repositorio descomprimido."
  exit 1
fi

echo "🐍 Entorno virtual..."
$PYTHON -m venv venv
source venv/bin/activate
stdbuf -oL -eL pip install --upgrade pip wheel
stdbuf -oL -eL pip install -r odoo-server/requirements.txt
stdbuf -oL -eL pip install gevent greenlet
echo "📦 Instalando dependencias adicionales comunes..."
stdbuf -oL -eL pip install phonenumbers

echo "🗑️ Limpiando base de datos existente si existe..."
sudo -u postgres dropdb "$INSTANCE_NAME" 2>/dev/null || true
echo "🛢️  Creando base de datos $INSTANCE_NAME..."
sudo -u postgres createdb "$INSTANCE_NAME" -O "$DB_USER" --encoding='UTF8'
echo "🔌 Instalando extensión vector..."
sudo -u postgres psql -d "$INSTANCE_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "⚙️ Generando archivo de configuración Odoo..."
cat > "$ODOO_CONF" <<EOF
[options]
addons_path = $BASE_DIR/odoo-server/addons,$BASE_DIR/custom_addons
db_host = localhost
db_port = 5432
db_user = $DB_USER
db_password = $DB_PASSWORD
db_name = $INSTANCE_NAME
log_level = info
logfile = $ODOO_LOG
http_port = $PORT
http_interface = 127.0.0.1
proxy_mode = True
admin_passwd = $ADMIN_PASSWORD
server_wide_modules = web,base,bus
gevent_port = $EVENTED_PORT
workers = 2
max_cron_threads = 1
db_maxconn = 8
EOF

touch "$ODOO_LOG"
chown -R $USER:$USER "$BASE_DIR"

echo "⚙️ Creando servicio systemd para Odoo..."
echo "[Unit]
Description=Odoo 19c Instance - $INSTANCE_NAME
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=$VENV_PYTHON $BASE_DIR/odoo-server/odoo-bin -c $ODOO_CONF
WorkingDirectory=$APP_DIR
StandardOutput=journal
StandardError=inherit
Restart=always

[Install]
WantedBy=multi-user.target
" | sudo tee /etc/systemd/system/odoo19c-$INSTANCE_NAME.service > /dev/null

if [ ! -f "/etc/systemd/system/odoo19c-$INSTANCE_NAME.service" ]; then
  echo "❌ Error crítico: No se pudo crear el archivo de servicio systemd"
  exit 1
fi

echo "🔄 Recargando systemd y habilitando servicio..."
sudo systemctl daemon-reload
echo "🌀 Habilitando servicio systemd (sin iniciar aún)..."
sudo systemctl enable "odoo19c-$INSTANCE_NAME"

# 6. Módulos y assets
echo "🔌 Cerrando conexiones existentes a la base de datos..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$INSTANCE_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true

echo "📦 Instalando módulos iniciales y configurando entorno Odoo..."
echo "   Esto puede tomar varios minutos..."
stdbuf -oL -eL sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" -c "$ODOO_CONF" --load-language=es_ES -i base,web,base_setup,contacts,l10n_latam_base,l10n_ar,l10n_ar_reports --without-demo=all --stop-after-init

if [ $? -ne 0 ]; then
  echo "❌ Error al instalar módulos iniciales. Revisa el log en $ODOO_LOG"
  exit 1
fi
echo "✅ Módulos iniciales instalados correctamente."

echo "🌎 Configurando idioma, zona horaria y moneda..."
sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" shell -d "$INSTANCE_NAME" <<EOFSHELL
lang = env['res.lang'].search([('code', '=', 'es_AR')], limit=1)
if lang:
    env.user.lang = 'es_AR'
    env.user.tz = 'America/Argentina/Buenos_Aires'
    env.user.company_id.write({'currency_id': env.ref('base.ARS').id})
EOFSHELL

echo "🎨 Actualizando módulos..."
stdbuf -oL -eL sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" -c "$ODOO_CONF" --update=all --stop-after-init

if [ $? -ne 0 ]; then
  echo "⚠️  Advertencia: Error al actualizar módulos. Continuando..."
fi

echo "🚀 Iniciando servicio Odoo..."
stdbuf -oL -eL sudo systemctl start "odoo19c-$INSTANCE_NAME"
sleep 3

if sudo systemctl is-active --quiet "odoo19c-$INSTANCE_NAME"; then
  echo "✅ Servicio Odoo iniciado correctamente."
else
  echo "❌ Error: El servicio no pudo iniciarse. Revisa los logs:"
  echo "   sudo journalctl -u odoo19c-$INSTANCE_NAME -n 50"
  exit 1
fi

# 7. Nginx y SSL
# Configurar SSL según la elección del usuario (ya preguntado al inicio)
configure_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$SSL_METHOD" "$EVENTED_PORT"

echo "📄 Generando archivo de información de la instancia..."
# 8. Info
cat > "$INFO_FILE" <<EOFINFO
🔧 Instancia: $INSTANCE_NAME
🌍 Dominio: https://$DOMAIN
🛠️ Puerto: $PORT
🧲 Evented port: $EVENTED_PORT
🗄️ Base de datos: $INSTANCE_NAME
👤 Usuario DB: $DB_USER
🔑 Contraseña DB: $DB_PASSWORD
📁 Ruta: $BASE_DIR
📄 Configuración: $ODOO_CONF
📝 Log: $ODOO_LOG
🪵 Log de instalación: $LOG
🧩 Servicio systemd: odoo19c-$INSTANCE_NAME
🌀 Logs: sudo journalctl -u odoo19c-$INSTANCE_NAME -n 50 --no-pager
🌐 Nginx: $NGINX_CONF
🕒 Zona horaria: America/Argentina/Buenos_Aires
🌐 IP pública: $PUBLIC_IP
🔁 Reiniciar servicio: sudo systemctl restart odoo19c-$INSTANCE_NAME
📋 Ver estado:         sudo systemctl status odoo19c-$INSTANCE_NAME
📦 Módulos instalados: base, web, base_setup, contacts, l10n_latam_base, l10n_ar, l10n_ar_reports
EOFINFO

# Registrar instancia en archivo de tracking
PROD_INSTANCES_FILE="${DATA_PATH}/prod-instances.txt"
echo "$INSTANCE_NAME|19|community|$DOMAIN|$PORT" >> "$PROD_INSTANCES_FILE"

echo "✅ Instancia creada con éxito: https://$DOMAIN"
# Marcar estado final como SUCCESS para el backend
STATUS_FILE="/tmp/$INSTANCE_NAME.status"
echo "success" > "$STATUS_FILE"
echo "📂 Ver detalles en: $BASE_DIR/info-instancia.txt"
