#!/bin/bash

# Script para resetear completamente la integración de Git en /home/mtg/api-dev
# Uso: ./reset-git-integration.sh

set -e

PROJECT_DIR="/home/mtg/api-dev"
GIT_DIR="$PROJECT_DIR/.git"

echo "=========================================="
echo "Reset de integración Git para API-DEV"
echo "=========================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: El directorio $PROJECT_DIR no existe"
    exit 1
fi

cd "$PROJECT_DIR"

# Backup de la configuración actual si existe
if [ -d "$GIT_DIR" ]; then
    echo "1. Haciendo backup de configuración Git actual..."
    BACKUP_DIR="$HOME/backups/git-config-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r "$GIT_DIR" "$BACKUP_DIR/"
    echo "   ✓ Backup guardado en: $BACKUP_DIR"
    echo ""
fi

# Eliminar configuración Git actual
if [ -d "$GIT_DIR" ]; then
    echo "2. Eliminando configuración Git actual..."
    rm -rf "$GIT_DIR"
    echo "   ✓ Directorio .git eliminado"
    echo ""
else
    echo "2. No existe configuración Git previa"
    echo ""
fi

# Limpiar configuraciones de remote que puedan estar corruptas
echo "3. Limpiando configuraciones globales de Git..."
git config --global --unset-all credential.helper 2>/dev/null || true
echo "   ✓ Credential helpers limpiados"
echo ""

# Reinicializar repositorio con la configuración correcta
echo "4. Reinicializando repositorio Git..."
git init
echo "   ✓ Repositorio inicializado"
echo ""

# Configurar usuario local
echo "5. Configurando usuario Git local..."
git config user.name "API Dev Panel"
git config user.email "dev@panel.local"
echo "   ✓ Usuario configurado"
echo ""

# Agregar remote con SSH (más seguro y sin problemas de tokens)
echo "6. Configurando remote origin..."
REMOTE_URL="git@github.com:mtriggiano/api-dev-softrigx.git"
git remote add origin "$REMOTE_URL"
echo "   ✓ Remote configurado: $REMOTE_URL"
echo ""

# Configurar rama principal
echo "7. Configurando rama principal..."
git branch -M main
echo "   ✓ Rama 'main' configurada"
echo ""

# Verificar estado
echo "8. Verificando configuración..."
echo ""
echo "Remote configurado:"
git remote -v
echo ""
echo "Rama actual:"
git branch
echo ""

echo "=========================================="
echo "✓ Reset completado exitosamente"
echo "=========================================="
echo ""
echo "PRÓXIMOS PASOS:"
echo "1. Verifica que tu clave SSH esté configurada en GitHub"
echo "2. Si necesitas hacer el primer commit:"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "3. Para sincronizar con el remoto:"
echo "   git pull origin main --allow-unrelated-histories"
echo "   git push -u origin main"
echo ""
echo "NOTA: Si prefieres usar HTTPS con token, edita manualmente"
echo "el remote con: git remote set-url origin https://github.com/mtriggiano/api-dev-softrigx.git"
echo ""
