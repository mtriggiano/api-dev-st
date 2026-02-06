#!/bin/bash

# Script para verificar y reparar la configuración del remote de Git
# Uso: ./fix-git-remote.sh

set -e

PROJECT_DIR="/home/mtg/api-dev"
EXPECTED_REMOTE="git@github.com:mtriggiano/api-dev-softrigx.git"

echo "=========================================="
echo "Verificación y reparación de Git Remote"
echo "=========================================="
echo ""

cd "$PROJECT_DIR"

# Verificar si existe .git
if [ ! -d ".git" ]; then
    echo "ERROR: No existe repositorio Git en $PROJECT_DIR"
    echo "Ejecuta primero: ./reset-git-integration.sh"
    exit 1
fi

# Obtener URL actual del remote
echo "1. Verificando remote actual..."
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

if [ -z "$CURRENT_REMOTE" ]; then
    echo "   ⚠ No existe remote 'origin'"
    echo "   Agregando remote..."
    git remote add origin "$EXPECTED_REMOTE"
    echo "   ✓ Remote agregado: $EXPECTED_REMOTE"
else
    echo "   Remote actual: $CURRENT_REMOTE"
    
    # Verificar si la URL está corrupta o tiene credenciales embebidas
    if [[ "$CURRENT_REMOTE" =~ @.*@|ghp_.*@.*/ ]]; then
        echo "   ⚠ URL corrupta detectada (contiene credenciales malformadas)"
        echo "   Reparando..."
        git remote set-url origin "$EXPECTED_REMOTE"
        echo "   ✓ Remote reparado: $EXPECTED_REMOTE"
    elif [[ "$CURRENT_REMOTE" == *"jaraba_addons"* ]]; then
        echo "   ⚠ URL incorrecta detectada (apunta a jaraba_addons)"
        echo "   Corrigiendo..."
        git remote set-url origin "$EXPECTED_REMOTE"
        echo "   ✓ Remote corregido: $EXPECTED_REMOTE"
    elif [ "$CURRENT_REMOTE" != "$EXPECTED_REMOTE" ]; then
        echo "   ⚠ URL diferente a la esperada"
        echo "   Esperada: $EXPECTED_REMOTE"
        echo "   Actual:   $CURRENT_REMOTE"
        read -p "   ¿Desea actualizar a la URL esperada? (s/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[SsYy]$ ]]; then
            git remote set-url origin "$EXPECTED_REMOTE"
            echo "   ✓ Remote actualizado: $EXPECTED_REMOTE"
        else
            echo "   Remote no modificado"
        fi
    else
        echo "   ✓ Remote correcto"
    fi
fi

echo ""
echo "2. Limpiando configuraciones corruptas..."
# Limpiar cualquier configuración de credential helper que pueda estar causando problemas
git config --local --unset-all credential.helper 2>/dev/null || true
git config --local --unset-all url.https://ghp_ 2>/dev/null || true
echo "   ✓ Configuraciones limpiadas"

echo ""
echo "3. Verificando conectividad SSH..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "   ✓ Autenticación SSH exitosa"
else
    echo "   ⚠ No se pudo autenticar con SSH"
    echo "   Verifica que tu clave SSH esté configurada en GitHub"
    echo "   Ejecuta: ssh -T git@github.com"
fi

echo ""
echo "4. Estado final:"
echo "   Remote: $(git remote get-url origin)"
echo "   Rama:   $(git branch --show-current 2>/dev/null || echo 'ninguna')"

echo ""
echo "=========================================="
echo "✓ Verificación completada"
echo "=========================================="
echo ""
echo "Si necesitas sincronizar con el remoto:"
echo "  git fetch origin"
echo "  git pull origin main --allow-unrelated-histories"
echo ""
