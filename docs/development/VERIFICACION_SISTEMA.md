# ✅ Verificación del Sistema - Multi-Instancias de Producción

## 🔧 Cambios Aplicados

### 1. Configuración de Sudoers ✅
- **Archivo**: `/etc/sudoers.d/odoo-scripts`
- **Usuario**: `mtg`
- **Permisos**: Scripts de Odoo, systemctl, nginx, certbot sin contraseña

**Verificar**:
```bash
sudo cat /etc/sudoers.d/odoo-scripts
```

### 2. Permisos de Archivos ✅
- **Archivo**: `/home/mtg/api-dev/data/prod-instances.txt`
- **Owner**: `mtg:mtg`
- **Permisos**: `664` (rw-rw-r--)

**Verificar**:
```bash
ls -la /home/mtg/api-dev/data/prod-instances.txt
```

### 3. Backend Modificado ✅
- **Archivo**: `/home/mtg/api-dev/backend/services/instance_manager.py`
- **Cambio**: Ejecuta script con `sudo` (línea 227)
- **SSL Default**: `letsencrypt` (línea 235)

**Verificar**:
```bash
grep -n "sudo.*script_path" /home/mtg/api-dev/backend/services/instance_manager.py
```

### 4. Frontend Actualizado ✅
- **SSL Default**: Let's Encrypt (Certbot)
- **Build**: Completado exitosamente

**Verificar**:
```bash
ls -lh /home/mtg/api-dev/frontend/dist/
```

## 🧪 Pruebas de Funcionamiento

### Prueba 1: Script desde Línea de Comandos (Sin Contraseña)

```bash
cd /home/mtg/api-dev
sudo ./scripts/odoo/create-prod-instance.sh test1
```

**Resultado Esperado**:
- ✅ No pide contraseña
- ✅ Muestra validación de variables
- ✅ Muestra opciones de SSL
- ✅ Dominio: `test1.softrigx.com`

### Prueba 2: Desde el Panel Web

1. Abrir panel web
2. Ir a "Instancias"
3. Clic en "Nueva Producción" (botón verde)
4. Ingresar nombre: `panel1`
5. SSL debe estar en "Let's Encrypt (Certbot)" por defecto
6. Clic en "Crear Producción"

**Resultado Esperado**:
- ✅ Modal se cierra
- ✅ Aparece ventana de log
- ✅ Log se actualiza cada 3 segundos
- ✅ Muestra progreso de creación

### Prueba 3: Verificar Log en Tiempo Real

```bash
# Mientras se crea una instancia
tail -f /tmp/odoo-create-prod-[nombre].log
```

**Resultado Esperado**:
- ✅ Log se actualiza en tiempo real
- ✅ Muestra cada paso de la creación
- ✅ Sin errores de permisos

## 🔍 Diagnóstico de Problemas

### Problema: "Log no disponible aún..."

**Causas posibles**:
1. El script no se ha iniciado
2. Permisos incorrectos en `/tmp/`
3. Backend no puede ejecutar sudo

**Solución**:
```bash
# Verificar que el script se está ejecutando
ps aux | grep create-prod-instance

# Verificar log manualmente
ls -la /tmp/odoo-create-prod-*.log

# Ver contenido del log
cat /tmp/odoo-create-prod-[nombre].log
```

### Problema: "Permission denied"

**Causas posibles**:
1. Archivo `prod-instances.txt` con permisos incorrectos
2. Sudoers no configurado correctamente

**Solución**:
```bash
# Arreglar permisos
sudo chown mtg:mtg /home/mtg/api-dev/data/prod-instances.txt
sudo chmod 664 /home/mtg/api-dev/data/prod-instances.txt

# Verificar sudoers
sudo visudo -c -f /etc/sudoers.d/odoo-scripts
```

### Problema: Script pide contraseña

**Causas posibles**:
1. Sudoers no instalado
2. Ruta del script incorrecta en sudoers

**Solución**:
```bash
# Reinstalar sudoers
cd /home/mtg/api-dev
sudo ./setup-sudoers.sh

# Verificar que funciona
sudo -n ./scripts/odoo/create-prod-instance.sh --help
```

## 📊 Estado del Sistema

### Backend
```bash
systemctl status server-panel-api
```
**Esperado**: `active (running)`

### Frontend
```bash
ls -lh /home/mtg/api-dev/frontend/dist/assets/
```
**Esperado**: Archivos `.js` y `.css` recientes

### Logs del Backend
```bash
tail -f /home/mtg/api-dev/logs/gunicorn-error.log
```
**Esperado**: Sin errores recientes

## 🚀 Comandos Útiles

### Ver instancias de producción
```bash
cat /home/mtg/api-dev/data/prod-instances.txt
```

### Ver puertos ocupados
```bash
cat /home/mtg/api-dev/data/puertos_ocupados_odoo.txt
```

### Listar servicios Odoo
```bash
systemctl list-units | grep odoo19e
```

### Ver logs de una instancia
```bash
sudo journalctl -u odoo19e-prod-[nombre] -n 50 --no-pager
```

### Reiniciar una instancia
```bash
sudo systemctl restart odoo19e-prod-[nombre]
```

## ✅ Checklist de Verificación

- [ ] Sudoers instalado y funcionando
- [ ] Permisos de `prod-instances.txt` correctos
- [ ] Backend reiniciado
- [ ] Frontend compilado
- [ ] Prueba desde línea de comandos exitosa
- [ ] Prueba desde panel web exitosa
- [ ] Logs visibles en tiempo real

## 📝 Notas Importantes

1. **Tiempo de creación**: 10-15 minutos por instancia
2. **SSL por defecto**: Let's Encrypt (Certbot)
3. **Dominio protegido**: `softrigx.com` nunca se modifica
4. **Subdominios**: Todas las instancias usan `[nombre].softrigx.com`
5. **Sin contraseña**: Configurado en sudoers para usuario `mtg`

## 🆘 Soporte

Si algo no funciona:
1. Revisar este documento
2. Verificar logs: `/tmp/odoo-create-prod-*.log`
3. Verificar backend: `/home/mtg/api-dev/logs/gunicorn-error.log`
4. Verificar permisos: `ls -la /home/mtg/api-dev/data/`

---

**Última actualización**: 18 Nov 2025
**Versión**: 1.0
