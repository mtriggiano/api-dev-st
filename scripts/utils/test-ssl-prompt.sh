#!/bin/bash

# Script de prueba para verificar el prompt SSL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/ssl-manager.sh"

echo "🧪 Probando función prompt_ssl_method..."
echo ""

SSL_METHOD=$(prompt_ssl_method)

echo ""
echo "✅ Resultado capturado: '$SSL_METHOD'"
echo ""

case $SSL_METHOD in
    1)
        echo "📝 Seleccionaste: Let's Encrypt (Certbot)"
        ;;
    2)
        echo "📝 Seleccionaste: Cloudflare Origin Certificate"
        ;;
    3)
        echo "📝 Seleccionaste: Solo HTTP"
        ;;
    *)
        echo "❌ Error: Valor inválido capturado"
        ;;
esac
