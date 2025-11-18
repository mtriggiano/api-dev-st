#!/bin/bash
#
# Script para resetear contraseña de usuario
# Uso: ./reset-password-api-dev.sh [username] [nueva_contraseña]
#

set -e

# Cargar variables de entorno
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_ROOT/scripts/utils/load-env.sh"

USERNAME=${1:-admin}
NEW_PASSWORD=${2}
BACKEND_DIR="${PROJECT_ROOT}/backend"

# Si no se proporciona contraseña, solicitarla
if [ -z "$NEW_PASSWORD" ]; then
    echo "🔐 Resetear contraseña para usuario: $USERNAME"
    echo ""
    read -sp "Nueva contraseña: " NEW_PASSWORD
    echo ""
    read -sp "Confirmar contraseña: " NEW_PASSWORD_CONFIRM
    echo ""
    
    if [ "$NEW_PASSWORD" != "$NEW_PASSWORD_CONFIRM" ]; then
        echo "❌ Las contraseñas no coinciden"
        exit 1
    fi
    
    if [ -z "$NEW_PASSWORD" ]; then
        echo "❌ La contraseña no puede estar vacía"
        exit 1
    fi
fi

echo ""
echo "🔄 Reseteando contraseña para usuario: $USERNAME"
echo ""

# Activar entorno virtual y ejecutar Python
cd "$BACKEND_DIR"
source venv/bin/activate

python3 << PYEOF
import sys
sys.path.insert(0, '${BACKEND_DIR}')
from flask import Flask
from config import Config
from models import db, User
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    user = User.query.filter_by(username='${USERNAME}').first()
    
    if user:
        user.password_hash = bcrypt.hashpw('${NEW_PASSWORD}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        print("✅ Contraseña reseteada exitosamente")
        print("")
        print("🔐 Credenciales:")
        print(f"   Usuario: {user.username}")
        print("   Contraseña: ********")
        print("")
    else:
        print(f"❌ Usuario '${USERNAME}' no encontrado")
        print("")
        print("Usuarios disponibles:")
        users = User.query.all()
        for u in users:
            print(f"   - {u.username}")
        exit(1)
PYEOF
