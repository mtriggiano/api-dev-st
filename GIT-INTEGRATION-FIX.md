# Solución para Problemas de Integración Git/GitHub

## Problema Identificado

El error que estás experimentando:
```
Error al conectar
La carpeta ya es un repositorio Git
Error al crear rama en remoto: fatal: unable to access 'https://github.com/mtriggiano/jaraba_addons.git/': URL rejected: Bad hostname
```

**Causas:**
1. URL del remote corrupta con credenciales malformadas
2. Token de GitHub embebido incorrectamente en la URL
3. Posible referencia a un repositorio incorrecto (`jaraba_addons` en lugar de `api-dev-softrigx`)

## Soluciones Implementadas

### 1. Código Corregido
Se corrigió `backend/services/git_manager.py` para:
- Limpiar URLs antes de agregar tokens
- Validar URLs correctamente usando `urllib.parse`
- Prevenir URLs malformadas con múltiples `@`

### 2. Scripts de Reparación

#### Opción A: Reparación Rápida (Recomendado)
```bash
cd /home/mtg/api-dev
./fix-git-remote.sh
```

Este script:
- Verifica la URL del remote actual
- Detecta y repara URLs corruptas automáticamente
- Limpia configuraciones problemáticas
- Verifica conectividad SSH

#### Opción B: Reset Completo
```bash
cd /home/mtg/api-dev
./reset-git-integration.sh
```

Este script:
- Hace backup de la configuración actual
- Elimina completamente `.git`
- Reinicializa el repositorio desde cero
- Configura el remote correctamente

### 3. Limpieza de Base de Datos

Si el problema persiste desde el panel web, limpia las configuraciones de GitHub en la BD:

```bash
cd /home/mtg/api-dev
python3 clean-github-db.py
```

Para ver todas las configuraciones:
```bash
python3 clean-github-db.py
```

Para eliminar configuración de una instancia específica:
```bash
python3 clean-github-db.py [nombre-instancia]
```

Para resetear (limpiar token y marcar como inactiva):
```bash
python3 clean-github-db.py --reset [nombre-instancia]
```

## Pasos Recomendados

### Solución Completa (Paso a Paso)

1. **Reparar el remote de Git:**
   ```bash
   cd /home/mtg/api-dev
   ./fix-git-remote.sh
   ```

2. **Limpiar configuraciones de GitHub en BD:**
   ```bash
   python3 clean-github-db.py
   # Revisar las configuraciones listadas
   # Si hay alguna corrupta, eliminarla
   ```

3. **Verificar que el remote esté correcto:**
   ```bash
   git remote -v
   # Debe mostrar: git@github.com:mtriggiano/api-dev-softrigx.git
   ```

4. **Verificar conectividad SSH:**
   ```bash
   ssh -T git@github.com
   # Debe mostrar: "Hi mtriggiano! You've successfully authenticated..."
   ```

5. **Sincronizar con el remoto (si es necesario):**
   ```bash
   git fetch origin
   git pull origin main --allow-unrelated-histories
   ```

6. **Reconfigurar desde el panel web:**
   - Accede al panel web de API-DEV
   - Ve a la sección de GitHub
   - Genera un nuevo token en GitHub (si el anterior expiró)
   - Configura la integración con el nuevo token

## Prevención de Problemas Futuros

### Usar SSH en lugar de HTTPS (Recomendado)
El remote está configurado con SSH (`git@github.com:...`) que es más seguro y no requiere tokens embebidos en URLs.

### Si necesitas usar HTTPS
Asegúrate de que:
- El token de GitHub sea válido
- No modifiques manualmente la URL del remote
- Dejes que el sistema maneje el token temporalmente

### Verificación Regular
```bash
# Verificar que el remote esté limpio
git remote get-url origin
# NO debe contener tokens ni credenciales embebidas
```

## Archivos Creados

- `fix-git-remote.sh` - Reparación rápida del remote
- `reset-git-integration.sh` - Reset completo de Git
- `clean-github-db.py` - Limpieza de configuraciones en BD
- `GIT-INTEGRATION-FIX.md` - Esta documentación

## Soporte Adicional

Si después de seguir estos pasos el problema persiste:

1. Verifica los logs del backend:
   ```bash
   tail -f /home/mtg/api-dev/backend/logs/*.log
   ```

2. Revisa el estado de Git:
   ```bash
   cd /home/mtg/api-dev
   git status
   git remote -v
   git config --list --local
   ```

3. Verifica que tu clave SSH esté en GitHub:
   - Ve a https://github.com/settings/keys
   - Asegúrate de que tu clave pública esté agregada

## Notas Importantes

- **Backup:** Todos los scripts hacen backup antes de modificar
- **Seguridad:** Nunca compartas tokens de GitHub
- **SSH vs HTTPS:** SSH es más seguro y no requiere tokens en URLs
- **Base de Datos:** Las configuraciones de GitHub se guardan en la BD y pueden causar conflictos si están corruptas
