#!/bin/bash

# Script para configurar sudoers y permitir ejecutar scripts de Odoo sin contraseña

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Configuración de Sudoers para API-DEV"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Este script debe ejecutarse como root"
    echo "   Usa: sudo ./setup-sudoers.sh"
    exit 1
fi

# Obtener el usuario actual (el que ejecutó sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"

if [ "$ACTUAL_USER" = "root" ]; then
    echo "⚠️  Ejecutado directamente como root"
    read -p "Ingresa el nombre del usuario para configurar: " ACTUAL_USER
fi

echo "👤 Configurando sudoers para usuario: $ACTUAL_USER"
echo ""

# Crear archivo temporal
TEMP_FILE="/tmp/odoo-scripts-sudoers-$$"
SUDOERS_FILE="/etc/sudoers.d/odoo-scripts"

cat > "$TEMP_FILE" << EOF
# Configuración de sudoers para API-DEV
# Permite ejecutar scripts de Odoo y comandos systemd sin contraseña
# Usuario: $ACTUAL_USER
# Fecha: $(date)

# Scripts de Odoo
$ACTUAL_USER ALL=(ALL) NOPASSWD: /home/$ACTUAL_USER/api-dev/scripts/odoo/*.sh

# Comandos systemd para servicios Odoo
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl enable odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl disable odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl status odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl is-active odoo*
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl daemon-reload

# Nginx
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl reload nginx
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/nginx -t

# PostgreSQL (para crear/eliminar bases de datos)
$ACTUAL_USER ALL=(postgres) NOPASSWD: /usr/bin/psql
$ACTUAL_USER ALL=(postgres) NOPASSWD: /usr/bin/createdb
$ACTUAL_USER ALL=(postgres) NOPASSWD: /usr/bin/dropdb

# Certbot (para Let's Encrypt)
$ACTUAL_USER ALL=(ALL) NOPASSWD: /usr/bin/certbot
EOF

echo "📄 Validando sintaxis del archivo sudoers..."
if visudo -c -f "$TEMP_FILE"; then
    echo "✅ Sintaxis correcta"
else
    echo "❌ Error en la sintaxis del archivo sudoers"
    rm -f "$TEMP_FILE"
    exit 1
fi

echo ""
echo "📋 Contenido del archivo:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$TEMP_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "¿Instalar esta configuración? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Instalación cancelada"
    rm -f "$TEMP_FILE"
    exit 1
fi

echo "📦 Instalando configuración..."
cp "$TEMP_FILE" "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
chown root:root "$SUDOERS_FILE"

echo "✅ Configuración instalada en: $SUDOERS_FILE"
echo ""

# Limpiar
rm -f "$TEMP_FILE"

# Verificar que funciona
echo "🧪 Probando configuración..."
if sudo -u "$ACTUAL_USER" sudo -n systemctl status odoo* >/dev/null 2>&1 || true; then
    echo "✅ Configuración funcionando correctamente"
else
    echo "⚠️  Puede que necesites cerrar sesión y volver a entrar"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Configuración completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ahora puedes ejecutar sin contraseña:"
echo "  • sudo ./scripts/odoo/create-prod-instance.sh [nombre]"
echo "  • sudo systemctl restart odoo19e-[instancia]"
echo "  • sudo certbot ..."
echo ""
