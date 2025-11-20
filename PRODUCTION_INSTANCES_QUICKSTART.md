# 🚀 Guía Rápida: Múltiples Instancias de Producción

## ✅ ¿Qué cambió?

Ahora puedes crear **múltiples instancias de Odoo en producción** en el mismo servidor, cada una con su propio subdominio.

## 🔒 Protección del Dominio Principal

**CRÍTICO**: El dominio principal `softrigx.com` está **PROTEGIDO**. 

- ✅ Todas las instancias se crean como **subdominios**
- ❌ **NUNCA** se modifica el dominio raíz
- ✅ Validaciones múltiples en script, backend y frontend

## 📝 Uso Rápido

### Desde el Panel Web (Recomendado)

1. Ir a **Instancias**
2. Clic en **"Nueva Producción"** (botón verde)
3. Ingresar nombre: `cliente1`
4. Seleccionar SSL: **Cloudflare** (recomendado)
5. Clic en **"Crear Producción"**

**Resultado**: Se creará `cliente1.softrigx.com`

### Desde Línea de Comandos

```bash
cd /home/mtg/api-dev
sudo ./scripts/odoo/create-prod-instance.sh cliente1
```

## 📋 Ejemplos

| Nombre Ingresado | Dominio Resultante | Instancia Interna |
|------------------|-------------------|-------------------|
| `cliente1` | `cliente1.softrigx.com` | `prod-cliente1` |
| `empresa-abc` | `empresa-abc.softrigx.com` | `prod-empresa-abc` |
| `testing` | `testing.softrigx.com` | `prod-testing` |

## ❌ Nombres Prohibidos

Estos nombres están **bloqueados** para proteger el dominio principal:

- `softrigx.com`
- `production`
- `prod`
- `www`
- `api`
- `mail`
- `ftp`

## 🔧 Gestión de Instancias

### Ver estado
```bash
sudo systemctl status odoo19e-prod-cliente1
```

### Reiniciar
```bash
sudo systemctl restart odoo19e-prod-cliente1
```

### Ver logs
```bash
sudo journalctl -u odoo19e-prod-cliente1 -n 50
```

### Ver información completa
```bash
cat /home/mtg/apps/production/odoo/prod-cliente1/info-instancia.txt
```

## 📁 Ubicación de Archivos

```
/home/mtg/apps/production/odoo/
├── prod-cliente1/          # Instancia 1
├── prod-cliente2/          # Instancia 2
└── prod-empresa-abc/       # Instancia 3
```

## 🌐 DNS y SSL

Cada instancia crea automáticamente:
- ✅ Registro DNS en Cloudflare
- ✅ Configuración Nginx
- ✅ Certificado SSL (según método elegido)
- ✅ Servicio systemd

## ⚠️ Consideraciones

### Recursos por Instancia
- **RAM**: ~500MB - 1GB
- **Disco**: ~2GB inicial
- **Puerto HTTP**: Asignado automáticamente (2100-3000)
- **Puerto Evented**: Asignado automáticamente (8072-8999)

### Tiempo de Creación
- **Producción**: 10-15 minutos
- **Desarrollo**: 5-10 minutos

## 🐛 Solución Rápida de Problemas

### Error al crear
```bash
# Ver log completo
cat /tmp/odoo-create-prod-[nombre].log
```

### Servicio no inicia
```bash
# Ver error
sudo journalctl -u odoo19e-prod-[nombre] -n 50

# Verificar puerto
lsof -i :[puerto]
```

### DNS no resuelve
```bash
# Verificar DNS
dig [nombre].softrigx.com @1.1.1.1
```

## 📚 Documentación Completa

Ver: `/home/mtg/api-dev/docs/MULTI_PRODUCTION_INSTANCES.md`

## 🔄 Actualizar Sistema

```bash
cd /home/mtg/api-dev
./update.sh
```

---

**¿Dudas?** Revisa la documentación completa o los logs de creación.
