# 🚀 Quick Start - Server Panel

## ⚠️ ANTES DE EMPEZAR: Dependencias del Sistema Linux

**IMPORTANTE**: Antes de crear instancias de Odoo, instala estas dependencias en el sistema Linux:

### wkhtmltopdf (CRÍTICO para PDFs en Odoo)

```bash
# Instalar wkhtmltopdf con Qt parcheado (requerido por Odoo)
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_amd64.deb
sudo apt install -y ./wkhtmltox_0.12.6.1-3.jammy_amd64.deb
rm wkhtmltox_0.12.6.1-3.jammy_amd64.deb

# Verificar instalación
wkhtmltopdf --version
# Debe mostrar: wkhtmltopdf 0.12.6.1 (with patched qt)
```

⚠️ **Sin wkhtmltopdf**: Los PDFs de Odoo (facturas, presupuestos, reportes) NO se generarán o saldrán sin formato.

📚 **Guía completa de dependencias**: [ODOO_DEPENDENCIES.md](ODOO_DEPENDENCIES.md)

---

## Despliegue en 3 Pasos

### 1️⃣ Ejecutar Script de Despliegue

```bash
cd /home/go/api
chmod +x deploy.sh
./deploy.sh
```

⏱️ **Tiempo estimado**: 5-10 minutos

### 2️⃣ Acceder al Panel

Abre tu navegador en: **https://api-dev.hospitalprivadosalta.ar**

### 3️⃣ Login

- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **Importante**: Cambia la contraseña después del primer login

---

## ✅ Verificación Rápida

```bash
# Backend funcionando?
sudo systemctl status server-panel-api

# Ver logs
sudo journalctl -u server-panel-api -f

# Test API
curl http://localhost:5000/health
```

---

## 🎯 Primeros Pasos

### Dashboard
- Ve métricas en tiempo real de CPU, RAM, Disco y Red
- Observa gráficos históricos

### Instancias
- Lista todas las instancias Odoo (producción y desarrollo)
- Crea una nueva instancia dev con un click
- Actualiza BD o archivos desde producción
- Reinicia o elimina instancias

### Logs
- Revisa el historial de todas las acciones
- Filtra por instancia, acción o período
- Ve estadísticas de éxito/errores

---

## 🆘 Problemas?

### Backend no inicia
```bash
sudo journalctl -u server-panel-api -n 50
```

### Error 502
```bash
sudo systemctl restart server-panel-api
sudo systemctl reload nginx
```

### No puedo acceder
- Verifica DNS en Cloudflare
- Espera 2-3 minutos para propagación
- Verifica certificado SSL: `sudo certbot certificates`

---

## 📚 Más Información

- **Guía completa**: [README.md](README.md)
- **Instalación manual**: [INSTALL.md](INSTALL.md)
- **Dependencias Odoo**: [ODOO_DEPENDENCIES.md](ODOO_DEPENDENCIES.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **API Endpoints**: Ver sección API en README.md

---

**¿Todo listo?** ¡Empieza a gestionar tu servidor! 🎉
