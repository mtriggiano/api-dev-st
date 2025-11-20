#!/bin/bash

# 🚀 Script de creación de instancia Odoo 19 Enterprise en PRODUCCIÓN
# IMPORTANTE: Este script SIEMPRE crea instancias en SUBDOMINIOS
# NUNCA usa el dominio raíz para proteger el dominio principal

set -e

# Asegurar PATH completo
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Cargar variables de entorno
SCRIPT_DIR="$(cd "$(/usr/bin/dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/load-env.sh"
source "$SCRIPT_DIR/../utils/ssl-manager.sh"

# Validar variables requeridas
source "$SCRIPT_DIR/../utils/validate-env.sh" \
    CF_API_TOKEN CF_ZONE_NAME DB_USER DB_PASSWORD \
    ODOO_ADMIN_PASSWORD PUBLIC_IP PROD_ROOT ODOO_REPO_PATH

# Validaciones de comandos
command -v jq >/dev/null 2>&1 || { echo >&2 "❌ 'jq' no está instalado."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo >&2 "❌ 'curl' no está instalado."; exit 1; }

# Variables desde .env
ODOO_ROOT="${PROD_ROOT}"
REPO="${ODOO_REPO_PATH}"
PYTHON="${PYTHON_BIN:-/usr/bin/python3.12}"
PUERTOS_FILE="${PUERTOS_FILE:-$DATA_PATH/puertos_ocupados_odoo.txt}"
PROD_INSTANCES_FILE="${DATA_PATH}/prod-instances.txt"
USER="${SYSTEM_USER}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
ADMIN_PASSWORD="${ODOO_ADMIN_PASSWORD}"
CF_API_TOKEN="${CF_API_TOKEN}"
CF_ZONE_NAME="${DOMAIN_ROOT}"
CF_EMAIL="${CF_EMAIL:-info@$CF_ZONE_NAME}"
PUBLIC_IP="${PUBLIC_IP}"

# Crear archivo de tracking si no existe
mkdir -p "$DATA_PATH"
touch "$PUERTOS_FILE"
touch "$PROD_INSTANCES_FILE"

# Obtener nombre de instancia y método SSL
RAW_NAME="$1"
SSL_METHOD="$2"  # Opcional: 1=letsencrypt, 2=cloudflare, 3=http

if [[ -z "$RAW_NAME" ]]; then 
    echo "❌ Debes pasar el nombre de la instancia (será usado como subdominio)."
    echo "   Ejemplo: ./create-prod-instance.sh cliente1 [ssl_method]"
    echo "   Creará: cliente1.softrigx.com"
    echo "   ssl_method: 1=Let's Encrypt (default), 2=Cloudflare, 3=HTTP"
    exit 1
fi

# Normalizar nombre (minúsculas, sin espacios)
INSTANCE=$(echo "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')

# VALIDACIÓN CRÍTICA: Verificar que no se intente usar el dominio raíz
if [[ "$INSTANCE" == "$CF_ZONE_NAME" ]] || [[ "$INSTANCE" == "production" ]] || [[ "$INSTANCE" == "prod" ]]; then
    echo "❌ ERROR CRÍTICO: No se puede usar ese nombre de instancia."
    echo "   El nombre '$INSTANCE' está reservado para proteger el dominio principal."
    echo "   Por favor usa un nombre diferente que será usado como subdominio."
    exit 1
fi

# Validar que el nombre sea válido para DNS
if [[ ! "$INSTANCE" =~ ^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$ ]]; then
    echo "❌ ERROR: Nombre de instancia inválido."
    echo "   Debe contener solo letras minúsculas, números y guiones."
    echo "   Debe comenzar y terminar con letra o número."
    exit 1
fi

INSTANCE_NAME="prod-$INSTANCE"
DOMAIN="$INSTANCE.$CF_ZONE_NAME"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 CREACIÓN DE INSTANCIA DE PRODUCCIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📛 Nombre instancia: $INSTANCE_NAME"
echo "🌐 Dominio: $DOMAIN"
echo "🏠 Dominio raíz protegido: $CF_ZONE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar si la instancia ya existe
if [[ -d "$ODOO_ROOT/$INSTANCE_NAME" ]]; then
    echo "⚠️  La instancia $INSTANCE_NAME ya existe en $ODOO_ROOT/$INSTANCE_NAME"
    read -p "¿Deseas recrearla? Esto eliminará la instancia existente (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "❌ Operación cancelada."
        exit 1
    fi
    echo "🗑️  Eliminando instancia existente..."
    sudo systemctl stop "odoo19e-$INSTANCE_NAME" 2>/dev/null || true
    sudo systemctl disable "odoo19e-$INSTANCE_NAME" 2>/dev/null || true
    sudo rm -f "/etc/systemd/system/odoo19e-$INSTANCE_NAME.service"
    sudo rm -f "/etc/nginx/sites-enabled/$INSTANCE_NAME"
    sudo rm -f "/etc/nginx/sites-available/$INSTANCE_NAME"
    sudo -u postgres dropdb "$INSTANCE_NAME" 2>/dev/null || true
    rm -rf "$ODOO_ROOT/$INSTANCE_NAME"
    sed -i "/^$INSTANCE_NAME$/d" "$PROD_INSTANCES_FILE" 2>/dev/null || true
fi

LOG="/tmp/odoo-create-$INSTANCE_NAME.log"
exec > >(tee -a "$LOG") 2>&1

echo "🚀 Iniciando creación de instancia Odoo: $INSTANCE_NAME"
echo ""

# Obtener método SSL (desde argumento o preguntar)
if [[ -z "$SSL_METHOD" ]]; then
    # Si no se pasó como argumento, preguntar
    SSL_METHOD=$(prompt_ssl_method)
    echo ""
fi

# Validar y normalizar SSL_METHOD
case "$SSL_METHOD" in
    1|letsencrypt|certbot)
        SSL_METHOD="1"
        ;;
    2|cloudflare)
        SSL_METHOD="2"
        ;;
    3|http|none)
        SSL_METHOD="3"
        ;;
    *)
        echo "⚠️  Método SSL inválido '$SSL_METHOD', usando Let's Encrypt por defecto"
        SSL_METHOD="1"
        ;;
esac

echo "✅ Método SSL seleccionado: $SSL_METHOD"
echo ""

# Cancelación segura
trap cleanup SIGINT
cleanup() {
  echo -e "\n❌ Cancelado por el usuario."
  [[ -d "$ODOO_ROOT/$INSTANCE_NAME" ]] && rm -rf "$ODOO_ROOT/$INSTANCE_NAME"
  sudo -u postgres dropdb "$INSTANCE_NAME" 2>/dev/null || true
  sed -i "/^$PORT$/d" "$PUERTOS_FILE" 2>/dev/null || true
  sed -i "/^$INSTANCE_NAME$/d" "$PROD_INSTANCES_FILE" 2>/dev/null || true
  exit 1
}

echo "🔍 Buscando puerto libre..."
# Buscar puerto libre
PORT=""
for p in {2100..3000}; do
  if ! grep -q "^$p$" "$PUERTOS_FILE" 2>/dev/null && ! lsof -iTCP:$p -sTCP:LISTEN -t >/dev/null; then
    PORT=$p
    break
  fi
done
[[ -z "$PORT" ]] && echo "❌ No hay puerto libre en rango 2100-3000." && exit 1
echo "✅ Puerto HTTP asignado: $PORT"

# Buscar puerto libre para evented/gevent (longpolling/websocket)
echo "🔍 Buscando puerto evented (gevent) libre..."
EVENTED_PORT=""
for ep in {8072..8999}; do
  if ! lsof -iTCP:$ep -sTCP:LISTEN -t >/dev/null; then
    EVENTED_PORT=$ep
    break
  fi
done
[[ -z "$EVENTED_PORT" ]] && echo "❌ No hay puerto evented libre (8072-8999)." && exit 1
echo "✅ Puerto evented asignado: $EVENTED_PORT"

BASE_DIR="$ODOO_ROOT/$INSTANCE_NAME"
SERVICE="/etc/systemd/system/odoo19e-$INSTANCE_NAME.service"
ODOO_CONF="$BASE_DIR/odoo.conf"
ODOO_LOG="$BASE_DIR/odoo.log"
NGINX_CONF="/etc/nginx/sites-available/$INSTANCE_NAME"
INFO_FILE="$BASE_DIR/info-instancia.txt"
VENV_DIR="$BASE_DIR/venv"
ODOO_BIN="$BASE_DIR/odoo-server/odoo-bin"
VENV_PYTHON="$VENV_DIR/bin/python3"
APP_DIR="$BASE_DIR"

# Configurar DNS en Cloudflare
echo "🌐 Configurando DNS en Cloudflare para $DOMAIN..."
echo "🌍 IP pública: $PUBLIC_IP"

CF_ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$CF_ZONE_NAME" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ -z "$CF_ZONE_ID" ] || [ "$CF_ZONE_ID" = "null" ]; then
  echo "❌ Error: No se pudo obtener el Zone ID de Cloudflare para $CF_ZONE_NAME"
  exit 1
fi

# Verificar si el registro DNS ya existe
EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records?name=$DOMAIN" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ ! -z "$EXISTING_RECORD" ] && [ "$EXISTING_RECORD" != "null" ]; then
  echo "⚠️  Registro DNS ya existe, actualizando..."
  curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records/$EXISTING_RECORD" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"type":"A","name":"'"$DOMAIN"'","content":"'"$PUBLIC_IP"'","ttl":3600,"proxied":true}' >/dev/null
  echo "✅ Registro DNS actualizado"
else
  DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    --data '{"type":"A","name":"'"$DOMAIN"'","content":"'"$PUBLIC_IP"'","ttl":3600,"proxied":true}')
  
  if echo "$DNS_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    echo "✅ Registro DNS creado exitosamente"
  else
    echo "⚠️  Advertencia: Posible error al crear registro DNS"
    echo "   Respuesta: $(echo $DNS_RESPONSE | jq -r '.errors[0].message' 2>/dev/null || echo 'Sin detalles')"
  fi
fi

# Esperar propagación DNS
echo "⏳ Esperando 5 segundos para propagación DNS..."
sleep 5

# Verificar DNS
echo "🛰️  Verificando propagación DNS..."
DNS_RESULT=$(dig +short "$DOMAIN" @1.1.1.1 2>/dev/null | head -1)
if [ ! -z "$DNS_RESULT" ]; then
  echo "✅ DNS resuelto a: $DNS_RESULT"
else
  echo "⚠️  DNS aún no visible, pero continuando..."
fi

# Crear estructura de carpetas
echo "📁 Creando estructura de carpetas en $BASE_DIR..."
mkdir -p "$BASE_DIR"
mkdir -p "$BASE_DIR/custom_addons"
mkdir -p "$BASE_DIR/odoo-server"

# Descomprimir repositorio
echo "📦 Descomprimiendo repositorio Odoo..."
unzip -q "$REPO" -d "$BASE_DIR/tmp_unzip"
cp "$BASE_DIR/tmp_unzip/setup.py" "$BASE_DIR/odoo-server/" 2>/dev/null || true
cp "$BASE_DIR/tmp_unzip/requirements19e.txt" "$BASE_DIR/odoo-server/requirements.txt" 2>/dev/null || true
cp -r "$BASE_DIR/tmp_unzip/odoo" "$BASE_DIR/odoo-server/"

# Copiar odoo-bin si existe
if [[ -f "$BASE_DIR/tmp_unzip/odoo-bin" ]]; then
  cp "$BASE_DIR/tmp_unzip/odoo-bin" "$BASE_DIR/odoo-server/"
  chmod +x "$BASE_DIR/odoo-server/odoo-bin"
fi

# Copiar setup si existe
if [[ -d "$BASE_DIR/tmp_unzip/setup" ]]; then
  cp -r "$BASE_DIR/tmp_unzip/setup" "$BASE_DIR/odoo-server/"
fi

rm -rf "$BASE_DIR/tmp_unzip"

# Verificar estructura
if [[ ! -d "$BASE_DIR/odoo-server/odoo" ]]; then
  echo "❌ Error: Carpeta 'odoo' no encontrada en el repositorio."
  exit 1
fi

# Crear odoo-bin si no existe
if [[ ! -f "$BASE_DIR/odoo-server/odoo-bin" ]]; then
  echo "⚠️  Creando odoo-bin..."
  cat > "$BASE_DIR/odoo-server/odoo-bin" <<'ODOOBIN'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

odoo_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, odoo_dir)

if __name__ == "__main__":
    from odoo.cli import main
    main()
ODOOBIN
  chmod +x "$BASE_DIR/odoo-server/odoo-bin"
  echo "✅ odoo-bin creado."
fi

# Crear entorno virtual
echo "🐍 Creando entorno virtual Python..."
$PYTHON -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "⬆️  Actualizando pip y wheel..."
pip install --upgrade pip wheel --quiet

echo "📦 Instalando dependencias Python..."
pip install -r "$BASE_DIR/odoo-server/requirements.txt" --quiet

echo "📦 Instalando dependencias adicionales..."
pip install phonenumbers qrcode pillow gevent greenlet --quiet

# Crear base de datos
echo "🗑️  Limpiando base de datos existente si existe..."
sudo -u postgres dropdb "$INSTANCE_NAME" 2>/dev/null || true

echo "🛢️  Creando base de datos $INSTANCE_NAME..."
sudo -u postgres createdb "$INSTANCE_NAME" -O "$DB_USER" --encoding='UTF8'

# Generar configuración Odoo
echo "⚙️  Generando configuración Odoo..."
cat > "$ODOO_CONF" <<EOF
[options]
addons_path = $BASE_DIR/odoo-server/odoo/addons,$BASE_DIR/custom_addons
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
workers = 2
max_cron_threads = 1
db_maxconn = 8
server_wide_modules = web,base,bus
gevent_port = $EVENTED_PORT
EOF

touch "$ODOO_LOG"
chown -R $USER:$USER "$BASE_DIR"

# Crear servicio systemd
echo "⚙️  Creando servicio systemd..."
cat > /tmp/odoo-service-$INSTANCE_NAME.service <<EOF
[Unit]
Description=Odoo 19e Production Instance - $INSTANCE_NAME ($DOMAIN)
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
ExecStart=$VENV_PYTHON $BASE_DIR/odoo-server/odoo-bin -c $APP_DIR/odoo.conf
WorkingDirectory=$APP_DIR
StandardOutput=journal
StandardError=inherit
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/odoo-service-$INSTANCE_NAME.service /etc/systemd/system/odoo19e-$INSTANCE_NAME.service

if [ ! -f "/etc/systemd/system/odoo19e-$INSTANCE_NAME.service" ]; then
  echo "❌ Error: No se pudo crear el servicio systemd"
  exit 1
fi

echo "🔄 Recargando systemd..."
sudo systemctl daemon-reload
sudo systemctl enable "odoo19e-$INSTANCE_NAME"

# Instalar módulos base
echo "🔌 Cerrando conexiones existentes..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$INSTANCE_NAME' AND pid <> pg_backend_pid();" 2>/dev/null || true

echo "📦 Instalando módulos iniciales (esto puede tomar varios minutos)..."
sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" -c "$ODOO_CONF" \
  --load-language=es_ES \
  -i base,web,base_setup,web_enterprise,contacts,l10n_latam_base,l10n_ar,l10n_ar_reports \
  --without-demo=all \
  --stop-after-init

if [ $? -ne 0 ]; then
  echo "❌ Error al instalar módulos. Ver log: $ODOO_LOG"
  exit 1
fi
echo "✅ Módulos instalados."

# Configurar idioma y zona horaria
echo "🌎 Configurando idioma y zona horaria..."
sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" shell -d "$INSTANCE_NAME" <<EOF
lang = env['res.lang'].search([('code', '=', 'es_AR')], limit=1)
if lang:
    env.user.lang = 'es_AR'
    env.user.tz = 'America/Argentina/Buenos_Aires'
    env.user.company_id.write({'currency_id': env.ref('base.ARS').id})
env.cr.commit()
EOF

# Actualizar módulos
echo "🎨 Actualizando módulos..."
sudo -u $USER "$VENV_PYTHON" "$BASE_DIR/odoo-server/odoo-bin" -c "$ODOO_CONF" \
  --update=all \
  --stop-after-init 2>&1 | grep -v "WARNING" || true

# Iniciar servicio
echo "🚀 Iniciando servicio Odoo..."
sudo systemctl start "odoo19e-$INSTANCE_NAME"
sleep 3

if sudo systemctl is-active --quiet "odoo19e-$INSTANCE_NAME"; then
  echo "✅ Servicio iniciado correctamente."
else
  echo "❌ Error: El servicio no pudo iniciarse."
  echo "   Ver logs: sudo journalctl -u odoo19e-$INSTANCE_NAME -n 50"
  exit 1
fi

# Configurar SSL y Nginx
echo "🔒 Configurando SSL y Nginx..."
configure_ssl "$DOMAIN" "$INSTANCE_NAME" "$PORT" "$SSL_METHOD" "$EVENTED_PORT"

# Registrar puerto e instancia
echo "$PORT" >> "$PUERTOS_FILE"
echo "$INSTANCE_NAME" >> "$PROD_INSTANCES_FILE"

# Generar archivo de información
cat > "$INFO_FILE" <<EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏭 INSTANCIA DE PRODUCCIÓN - $INSTANCE_NAME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Información General
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📛 Nombre instancia: $INSTANCE_NAME
🌐 Dominio: https://$DOMAIN
🏠 Dominio raíz (protegido): $CF_ZONE_NAME
🛠️  Puerto HTTP: $PORT
🔌 Puerto Evented: $EVENTED_PORT
🗄️  Base de datos: $INSTANCE_NAME
👤 Usuario DB: $DB_USER
🔑 Contraseña DB: $DB_PASSWORD

📁 Rutas del Sistema
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📂 Ruta base: $BASE_DIR
📄 Configuración: $ODOO_CONF
📝 Log Odoo: $ODOO_LOG
🪵 Log instalación: $LOG
🌐 Nginx config: $NGINX_CONF

🔧 Gestión del Servicio
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧩 Servicio: odoo19e-$INSTANCE_NAME
🔁 Reiniciar: sudo systemctl restart odoo19e-$INSTANCE_NAME
⏹️  Detener: sudo systemctl stop odoo19e-$INSTANCE_NAME
▶️  Iniciar: sudo systemctl start odoo19e-$INSTANCE_NAME
📋 Estado: sudo systemctl status odoo19e-$INSTANCE_NAME
🌀 Logs: sudo journalctl -u odoo19e-$INSTANCE_NAME -n 50 --no-pager

🌍 Información de Red
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 IP pública: $PUBLIC_IP
🕒 Zona horaria: America/Argentina/Buenos_Aires
🔒 SSL: $SSL_METHOD

📦 Módulos Instalados
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
base, web, web_enterprise, base_setup, contacts
l10n_latam_base, l10n_ar, l10n_ar_reports

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Instancia creada: $(date)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ¡INSTANCIA CREADA EXITOSAMENTE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Accede a: https://$DOMAIN"
echo "📂 Detalles en: $BASE_DIR/info-instancia.txt"
echo "🪵 Log completo: $LOG"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
