# 🔄 Script de Reinicio de Servicios

Script para reiniciar fácilmente el backend y frontend de API-DEV.

## 📍 Ubicación

- **Script principal**: `/home/mtg/api-dev/scripts/utils/restart-services.sh`
- **Atajo rápido**: `/home/mtg/api-dev/restart.sh`

## 🚀 Uso

### Desde la raíz del proyecto:

```bash
# Reiniciar ambos servicios (backend + frontend)
./restart.sh

# Solo backend
./restart.sh backend

# Solo frontend
./restart.sh frontend

# Ver estado de servicios
./restart.sh status
```

### Desde cualquier lugar:

```bash
# Reiniciar ambos
/home/mtg/api-dev/restart.sh

# Solo backend
/home/mtg/api-dev/restart.sh backend

# Solo frontend
/home/mtg/api-dev/restart.sh frontend

# Ver estado
/home/mtg/api-dev/restart.sh status
```

## 📝 Opciones

| Comando | Alias | Descripción |
|---------|-------|-------------|
| `all` | `a` o sin parámetro | Reinicia backend y frontend |
| `backend` | `back`, `b` | Reinicia solo el backend |
| `frontend` | `front`, `f` | Reinicia solo el frontend |
| `status` | `s` | Muestra el estado de los servicios |

## 💡 Ejemplos

```bash
# Reiniciar todo después de hacer cambios
./restart.sh

# Solo reiniciar backend después de modificar Python
./restart.sh backend

# Solo reiniciar frontend después de modificar React
./restart.sh frontend

# Verificar que todo esté corriendo
./restart.sh status
```

## 🔍 Qué hace el script

### Backend
1. Busca el proceso master de gunicorn
2. Si está corriendo: envía señal HUP para reiniciar workers
3. Si no está corriendo: lo inicia con la configuración correcta
4. Verifica que esté corriendo correctamente
5. Muestra las últimas líneas del log

### Frontend
1. Detiene cualquier proceso `npm run dev` existente
2. Inicia un nuevo proceso con `npm run dev`
3. Verifica que esté corriendo correctamente
4. Muestra las últimas líneas del log de Vite

## 📊 Salida del comando `status`

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Estado de Servicios API-DEV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Backend: Corriendo (PID: 1993180)
   Puerto: 127.0.0.1:5000
✅ Frontend: Corriendo (PID: 2645048)
   URL: http://localhost:5173/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🛠️ Logs

- **Backend**: `/home/mtg/api-dev/logs/gunicorn-error.log`
- **Frontend**: `/tmp/frontend-dev.log`

## ⚠️ Notas

- El script usa `set -e` para detenerse ante cualquier error
- El backend se reinicia con HUP (graceful restart) si ya está corriendo
- El frontend se detiene completamente y se reinicia desde cero
- Los logs se muestran automáticamente después de cada reinicio
