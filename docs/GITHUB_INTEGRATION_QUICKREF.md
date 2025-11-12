# 🚀 GitHub Integration - Quick Reference

Referencia rápida para la integración de GitHub en API-DEV.

---

## ⚡ Inicio Rápido

### 1. Verificar Requisitos
```bash
# Git debe estar en /usr/bin/git
ls -la /usr/bin/git

# Si no está, instalarlo
sudo apt update && sudo apt install git -y
```

### 2. Crear Token de GitHub
1. Ve a: https://github.com/settings/tokens
2. Click en "Generate new token (classic)"
3. Marca el scope **`repo`** (completo)
4. Copia el token (empieza con `ghp_`)

### 3. Conectar desde el Panel Web
1. Abre el panel de API-DEV
2. Selecciona tu instancia de desarrollo
3. Click en el botón de GitHub
4. Ingresa:
   - **Token**: Tu token de GitHub
   - **URL del repo**: `https://github.com/usuario/repositorio`
5. Click en "Conectar"

---

## 🔧 Comandos Útiles

### Verificar Estado
```bash
# Ver si Git está instalado correctamente
which git
git --version

# Ver estado del servicio API
sudo systemctl status server-panel-api

# Ver logs en tiempo real
sudo journalctl -u server-panel-api -f
```

### Reiniciar Servicio
```bash
sudo systemctl restart server-panel-api
```

### Verificar Configuración
```bash
# Ver configuraciones de GitHub en la DB
cd /home/go/api-dev/backend
source venv/bin/activate
python3 << 'EOF'
from app import create_app
from models import GitHubConfig
app = create_app()
with app.app_context():
    configs = GitHubConfig.query.all()
    for c in configs:
        print(f"Instancia: {c.instance_name}, Repo: {c.repo_owner}/{c.repo_name}, Activa: {c.is_active}")
EOF
```

---

## 🐛 Problemas Comunes

### Error: "No such file or directory: 'git'"
**Solución:**
```bash
sudo apt install git -y
sudo systemctl restart server-panel-api
```

### Error: "Token de GitHub inválido"
**Solución:**
1. Genera un nuevo token en GitHub
2. Asegúrate de marcar el scope `repo`
3. Actualiza la configuración en el panel

### Error: "La carpeta ya es un repositorio Git"
**Solución:**
- Si quieres mantener el repo: No uses "Conectar", ya está conectado
- Si quieres empezar de cero: Elimina la configuración y vuelve a conectar

### Error: "No es un repositorio Git"
**Solución:**
1. Elimina la configuración desde el panel
2. Vuelve a conectar desde cero
3. El sistema inicializará el repositorio automáticamente

---

## 📋 Checklist de Instalación

- [ ] Git instalado en `/usr/bin/git`
- [ ] Token de GitHub creado con scope `repo`
- [ ] Repositorio creado en GitHub
- [ ] Carpeta `custom_addons` existe en la instancia
- [ ] Usuario tiene permisos de escritura en el repositorio
- [ ] Servicio `server-panel-api` está activo

---

## 🔗 Enlaces Útiles

- [Documentación completa](GITHUB_INTEGRATION.md)
- [Crear token de GitHub](https://github.com/settings/tokens)
- [Changelog del proyecto](../CHANGELOG.md)
- [README principal](../README.md)

---

## 💡 Tips

### Usar Ramas por Instancia
Cada instancia de desarrollo usa su propio nombre como rama:
- Instancia `dev-mtg` → Rama `dev-mtg`
- Instancia `dev-test` → Rama `dev-test`

Esto permite que múltiples desarrolladores trabajen en el mismo repositorio sin conflictos.

### Commits Automáticos
El sistema configura automáticamente:
- **User**: `API Dev Panel`
- **Email**: `dev@panel.local`

Puedes cambiar esto en cada commit desde el panel.

### Seguridad de Tokens
- Los tokens se almacenan en la base de datos
- En producción, considera encriptarlos
- Rota los tokens periódicamente
- No compartas tokens entre usuarios

---

**Última actualización:** 2025-11-12  
**Versión:** 2.1
