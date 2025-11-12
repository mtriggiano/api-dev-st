#!/bin/bash
#
# Script para cambiar contraseña de usuario en API-DEV
# Uso: ./change-password.sh [username] [nueva_contraseña]
#

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║   API-DEV - Cambiar Contraseña         ║"
echo "╔════════════════════════════════════════╗"
echo -e "${NC}"

# Verificar si estamos en el directorio correcto
if [ ! -f "/home/go/api-dev/backend/models.py" ]; then
    echo -e "${RED}❌ Error: Este script debe ejecutarse desde el servidor API-DEV${NC}"
    exit 1
fi

# Función para listar usuarios
list_users() {
    echo -e "${BLUE}📋 Usuarios disponibles:${NC}"
    python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/go/api-dev/backend')
from flask import Flask
from config import Config
from models import db, User

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    users = User.query.all()
    if not users:
        print("   No hay usuarios en la base de datos")
    else:
        for u in users:
            print(f"   - {u.username} (ID: {u.id}, Role: {u.role})")
PYEOF
}

# Función para cambiar contraseña
change_password() {
    local username=$1
    local password=$2
    
    python3 << PYEOF
import sys
sys.path.insert(0, '/home/go/api-dev/backend')
from flask import Flask
from config import Config
from models import db, User
import bcrypt

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    user = User.query.filter_by(username='${username}').first()
    
    if user:
        user.password_hash = bcrypt.hashpw('${password}'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        print(f"✅ Contraseña actualizada exitosamente")
        print(f"   Usuario: {user.username}")
        print(f"   Role: {user.role}")
        exit(0)
    else:
        print(f"❌ Usuario '${username}' no encontrado")
        exit(1)
PYEOF
}

# Si se proporcionan argumentos
if [ $# -eq 2 ]; then
    USERNAME=$1
    PASSWORD=$2
    echo -e "${YELLOW}Cambiando contraseña para usuario: ${USERNAME}${NC}"
    echo ""
    if change_password "$USERNAME" "$PASSWORD"; then
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║         ¡Contraseña Actualizada!       ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}🔐 Nuevas credenciales:${NC}"
        echo -e "   Usuario: ${GREEN}${USERNAME}${NC}"
        echo -e "   Contraseña: ${GREEN}${PASSWORD}${NC}"
        echo ""
    fi
    exit 0
fi

# Modo interactivo
echo ""
list_users
echo ""

# Solicitar nombre de usuario
echo -e "${YELLOW}Ingresa el nombre de usuario:${NC}"
read -p "👤 Usuario: " USERNAME

if [ -z "$USERNAME" ]; then
    echo -e "${RED}❌ Error: Debes ingresar un nombre de usuario${NC}"
    exit 1
fi

# Solicitar contraseña
echo ""
echo -e "${YELLOW}Ingresa la nueva contraseña:${NC}"
read -sp "🔒 Contraseña: " PASSWORD
echo ""

if [ -z "$PASSWORD" ]; then
    echo -e "${RED}❌ Error: Debes ingresar una contraseña${NC}"
    exit 1
fi

# Confirmar contraseña
read -sp "🔒 Confirmar contraseña: " PASSWORD_CONFIRM
echo ""

if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
    echo -e "${RED}❌ Error: Las contraseñas no coinciden${NC}"
    exit 1
fi

# Cambiar contraseña
echo ""
echo -e "${YELLOW}Actualizando contraseña...${NC}"
if change_password "$USERNAME" "$PASSWORD"; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         ¡Contraseña Actualizada!       ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}🔐 Nuevas credenciales:${NC}"
    echo -e "   Usuario: ${GREEN}${USERNAME}${NC}"
    echo -e "   Contraseña: ${GREEN}${PASSWORD}${NC}"
    echo ""
    echo -e "${BLUE}💡 Tip: Puedes usar este script de forma no interactiva:${NC}"
    echo -e "   ${YELLOW}./change-password.sh ${USERNAME} nueva_contraseña${NC}"
    echo ""
fi
