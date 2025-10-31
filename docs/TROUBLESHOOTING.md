# 🔧 Troubleshooting - Server Panel

## Problemas Comunes y Soluciones

### ❌ Error 500 - Permission Denied

**Síntoma:**
- Navegador muestra "500 Internal Server Error"
- Logs de Nginx: `stat() "/home/go/api/frontend/dist/" failed (13: Permission denied)`

**Causa:**
Nginx no tiene permisos para leer los archivos del frontend en `/home/go/api/frontend/dist/`

**Solución:**
```bash
# Dar permisos de lectura a Nginx
chmod -R 755 /home/go/api/frontend/dist
chmod 755 /home/go /home/go/api /home/go/api/frontend

# Recargar Nginx
sudo systemctl reload nginx
```

**Verificación:**
```bash
# Debe devolver 200 OK
curl -I https://api-dev.hospitalprivadosalta.ar/
```

---

### ❌ Backend no inicia

**Síntoma:**
- `systemctl status server-panel-api` muestra "failed"
- No responde en puerto 5000

**Diagnóstico:**
```bash
# Ver logs detallados
sudo journalctl -u server-panel-api -n 100 --no-pager

# Verificar puerto
sudo lsof -i :5000
```

**Soluciones comunes:**

1. **Error de base de datos:**
```bash
# Verificar que la BD existe
sudo -u postgres psql -l | grep server_panel

# Recrear si es necesario
sudo -u postgres dropdb server_panel
sudo -u postgres createdb server_panel -O go --encoding='UTF8'
cd /home/go/api/backend
source venv/bin/activate
python3 -c "from app import create_app, init_db; app = create_app(); init_db(app)"
```

2. **Error en variables de entorno:**
```bash
# Verificar .env
cat /home/go/api/backend/.env

# Verificar que tenga SECRET_KEY y JWT_SECRET_KEY
```

3. **Dependencias faltantes:**
```bash
cd /home/go/api/backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart server-panel-api
```

---

### ❌ Frontend no carga (pantalla en blanco)

**Síntoma:**
- Página carga pero está en blanco
- Console del navegador muestra errores

**Solución:**
```bash
# Reconstruir frontend
cd /home/go/api/frontend
npm install
npm run build

# Ajustar permisos
chmod -R 755 /home/go/api/frontend/dist

# Recargar Nginx
sudo systemctl reload nginx
```

---

### ❌ Error de CORS

**Síntoma:**
- Console del navegador: "CORS policy blocked"
- API responde pero el frontend no puede acceder

**Solución:**
Verificar que el dominio esté en la lista de CORS permitidos:

```python
# En /home/go/api/backend/config.py
CORS_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'https://api-dev.hospitalprivadosalta.ar'
]
```

Reiniciar backend:
```bash
sudo systemctl restart server-panel-api
```

---

### ❌ JWT Token Expirado

**Síntoma:**
- Usuario logueado es redirigido al login
- API responde con 401 Unauthorized

**Solución:**
Esto es normal después de 8 horas. El usuario debe hacer login nuevamente.

Para cambiar la duración del token:
```python
# En /home/go/api/backend/config.py
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Cambiar a 24 horas
```

---

### ❌ Certificado SSL no se genera

**Síntoma:**
- Certbot falla al obtener certificado
- Sitio no accesible por HTTPS

**Diagnóstico:**
```bash
# Verificar DNS
dig api-dev.hospitalprivadosalta.ar

# Debe apuntar a 200.69.140.2
```

**Solución:**
```bash
# Intentar manualmente
sudo certbot --nginx -d api-dev.hospitalprivadosalta.ar

# Si falla, verificar que el puerto 80 esté abierto
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

### ❌ Métricas no se guardan

**Síntoma:**
- Gráficos históricos vacíos
- No hay datos en `metrics_history`

**Diagnóstico:**
```bash
# Verificar cron job
crontab -l | grep metrics

# Probar manualmente
curl -X POST http://localhost:5000/api/metrics/save
```

**Solución:**
```bash
# Agregar cron job si no existe
crontab -e

# Agregar línea:
* * * * * curl -X POST http://localhost:5000/api/metrics/save >/dev/null 2>&1

# Verificar logs de cron
grep CRON /var/log/syslog | tail -20
```

---

### ❌ Instancias no se listan

**Síntoma:**
- Panel de instancias vacío
- API devuelve array vacío

**Causa:**
Las rutas en `config.py` no coinciden con la estructura real

**Solución:**
```bash
# Verificar rutas en config.py
cat /home/go/api/backend/.env

# Verificar que existan:
ls -la /home/go/apps/production/odoo/
ls -la /home/go/apps/develop/odoo/
```

---

### ❌ No puedo crear instancias

**Síntoma:**
- Botón "Crear Instancia" no funciona
- Error 403 Forbidden

**Causa:**
Usuario no tiene permisos (rol viewer)

**Solución:**
Cambiar rol del usuario a developer o admin:

```bash
cd /home/go/api/backend
source venv/bin/activate
python3
```

```python
from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='tu_usuario').first()
    user.role = 'admin'  # o 'developer'
    db.session.commit()
    print(f"Usuario {user.username} ahora es {user.role}")
```

---

### ❌ Logs no se muestran

**Síntoma:**
- Sección de logs vacía
- No hay registros de acciones

**Causa:**
Las acciones no se están registrando en la BD

**Verificación:**
```bash
sudo -u postgres psql -d server_panel -c "SELECT COUNT(*) FROM action_logs;"
```

**Solución:**
Si la tabla está vacía, realizar alguna acción (crear instancia, reiniciar, etc.) y verificar nuevamente.

---

### ❌ Puerto 5000 ocupado

**Síntoma:**
- Backend no puede iniciar
- Error: "Address already in use"

**Solución:**
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :5000

# Matar proceso si es necesario
sudo kill -9 <PID>

# O cambiar el puerto en el servicio systemd
sudo nano /etc/systemd/system/server-panel-api.service
# Cambiar -b 127.0.0.1:5000 por otro puerto

sudo systemctl daemon-reload
sudo systemctl restart server-panel-api
```

---

## 🔍 Comandos de Diagnóstico Rápido

```bash
# Estado general
sudo systemctl status server-panel-api
sudo systemctl status nginx

# Logs
sudo journalctl -u server-panel-api -n 50
sudo tail -50 /var/log/nginx/error.log

# Test backend
curl http://localhost:5000/health

# Test frontend
curl -I https://api-dev.hospitalprivadosalta.ar/

# Test API
curl -X POST https://api-dev.hospitalprivadosalta.ar/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Ver BD
sudo -u postgres psql -d server_panel
\dt
SELECT * FROM users;
\q

# Permisos
ls -la /home/go/api/frontend/dist/
ls -la /home/go/api/backend/

# Procesos
ps aux | grep gunicorn
ps aux | grep nginx
```

---

## 📞 Si nada funciona

1. **Revisar logs completos:**
```bash
sudo journalctl -u server-panel-api -n 200 --no-pager > backend_logs.txt
sudo tail -200 /var/log/nginx/error.log > nginx_logs.txt
```

2. **Reiniciar todo:**
```bash
sudo systemctl restart server-panel-api
sudo systemctl restart nginx
```

3. **Redesplegar:**
```bash
cd /home/go/api
./deploy.sh
```

4. **Verificar documentación:**
- README.md
- INSTALL.md
- COMMANDS.md

---

**Última actualización:** 2025-10-28
