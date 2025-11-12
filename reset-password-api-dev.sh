#!/bin/bash
#
# Script rápido para resetear contraseña a 'go'
# Uso: ./reset-password.sh [username]
#

USERNAME=${1:-admin}

echo "🔄 Reseteando contraseña para usuario: $USERNAME"
echo ""

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
    user = User.query.filter_by(username='${USERNAME}').first()
    
    if user:
        user.password_hash = bcrypt.hashpw('go'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.session.commit()
        print("✅ Contraseña reseteada exitosamente")
        print("")
        print("🔐 Credenciales:")
        print(f"   Usuario: {user.username}")
        print("   Contraseña: go")
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
