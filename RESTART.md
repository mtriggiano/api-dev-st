# 🔄 Script de Reinicio de Servicios

Script para reiniciar fácilmente el backend y frontend de API-DEV.

## 📍 Ubicación

- **Script principal**: `/home/mtg/api-dev/scripts/utils/restart-services.sh`
- **Atajo rápido**: `/home/mtg/api-dev/restart.sh`

## 🚀 Uso

### Desde la raíz del proyecto:

```bash
# Aplicar cambios locales (rebuild + restart) - recomendado
./restart.sh

# Reinicio rápido (solo reinicia procesos, sin rebuild)
./restart.sh quick

# Solo backend
./restart.sh backend

# Solo frontend
./restart.sh frontend

# Ver estado de servicios
./restart.sh status
```

### Desde cualquier lugar:

```bash
# Aplicar cambios locales (rebuild + restart) - recomendado
/home/mtg/api-dev/restart.sh

# Reinicio rápido (solo reinicia procesos, sin rebuild)
/home/mtg/api-dev/restart.sh quick

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
| *(sin parámetro)* |  | Update local (build + restart) usando `update.sh --local --non-interactive` |
| `update` |  | Igual que sin parámetro (update local) |
| `quick` |  | Reinicio rápido (solo reinicia procesos, sin rebuild) |
| `all` | `a` | Reinicia backend y frontend (equivalente a `restart-services.sh all`) |
| `backend` | `back`, `b` | Reinicia solo el backend |
| `frontend` | `front`, `f` | Reinicia solo el frontend |
| `status` | `s` | Muestra el estado de los servicios |

## 💡 Ejemplos

```bash
# Aplicar cambios locales después de modificar código
./restart.sh

# Reinicio rápido (cuando no necesitás rebuild)
./restart.sh quick

# Solo reiniciar backend después de modificar Python
./restart.sh backend

# Solo reiniciar frontend después de modificar React
./restart.sh frontend

# Verificar que todo esté corriendo
./restart.sh status
```

## 🔍 Qué hace el script

### Modo default (sin argumentos)
Ejecuta un update local no interactivo:
- `./update.sh --local --non-interactive`

Este modo:
- No hace `git pull`
- Construye frontend
- Reinicia backend
- Reinicia frontend dev (Vite) y libera el puerto 5173 si está ocupado

### Modo quick
`./restart.sh quick` ejecuta el reinicio clásico (sin rebuild) usando `restart-services.sh`.

### Backend
1. Busca el proceso master de gunicorn
2. Si está corriendo: envía señal HUP para reiniciar workers
3. Si no está corriendo: lo inicia con la configuración correcta
4. Verifica que esté corriendo correctamente
5. Muestra las últimas líneas del log

### Frontend
1. Detiene cualquier proceso `npm run dev` existente
2. Libera el puerto 5173 si está ocupado
3. Inicia un nuevo proceso con `npm run dev` forzando puerto 5173
3. Verifica que esté corriendo correctamente
4. Muestra las últimas líneas del log de Vite

## 🔁 Update (relación con update.sh)

`update.sh` soporta dos modos:
- `./update.sh` o `./update.sh --github`: actualiza desde GitHub (pull)
- `./update.sh --local`: aplica cambios locales (sin pull)

Y un modo no interactivo:
- `./update.sh --local --non-interactive`

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
