#!/home/mtg/api-dev/backend/venv/bin/python3
"""
Script para limpiar configuraciones de GitHub corruptas en la base de datos
Uso: /home/mtg/api-dev/backend/venv/bin/python3 clean-github-db.py [instance_name]
O: cd /home/mtg/api-dev && source backend/venv/bin/activate && python3 clean-github-db.py
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, '/home/mtg/api-dev/backend')

from app import create_app
from models import db, GitHubConfig
from datetime import datetime

# Crear instancia de la app
app = create_app()

def clean_github_config(instance_name=None):
    """Limpia configuraciones de GitHub"""
    with app.app_context():
        if instance_name:
            # Limpiar configuración específica
            configs = GitHubConfig.query.filter_by(instance_name=instance_name).all()
            print(f"\nBuscando configuraciones para: {instance_name}")
        else:
            # Listar todas las configuraciones
            configs = GitHubConfig.query.all()
            print("\nListando todas las configuraciones de GitHub:")
        
        if not configs:
            print("No se encontraron configuraciones.")
            return
        
        print(f"\nEncontradas {len(configs)} configuración(es):\n")
        
        for i, config in enumerate(configs, 1):
            print(f"{i}. Instancia: {config.instance_name}")
            print(f"   Usuario: {config.github_username}")
            print(f"   Repo: {config.repo_owner}/{config.repo_name}")
            print(f"   Rama: {config.repo_branch}")
            print(f"   Path: {config.local_path}")
            print(f"   Activa: {config.is_active}")
            print(f"   Creada: {config.created_at}")
            print(f"   Actualizada: {config.updated_at}")
            print()
        
        if instance_name:
            # Preguntar si desea eliminar
            response = input(f"\n¿Desea ELIMINAR todas las configuraciones de '{instance_name}'? (si/no): ")
            if response.lower() in ['si', 'sí', 's', 'yes', 'y']:
                for config in configs:
                    db.session.delete(config)
                db.session.commit()
                print(f"\n✓ {len(configs)} configuración(es) eliminada(s) exitosamente.")
            else:
                print("\nOperación cancelada.")
        else:
            print("\nPara eliminar una configuración específica, ejecuta:")
            print("python3 clean-github-db.py [instance_name]")

def reset_config(instance_name):
    """Resetea una configuración específica (marca como inactiva y limpia token)"""
    with app.app_context():
        config = GitHubConfig.query.filter_by(instance_name=instance_name).first()
        
        if not config:
            print(f"\nNo se encontró configuración para: {instance_name}")
            return
        
        print(f"\nConfiguracion actual:")
        print(f"  Instancia: {config.instance_name}")
        print(f"  Usuario: {config.github_username}")
        print(f"  Repo: {config.repo_owner}/{config.repo_name}")
        print(f"  Activa: {config.is_active}")
        
        response = input(f"\n¿Desea RESETEAR esta configuración? (limpia token y marca como inactiva) (si/no): ")
        if response.lower() in ['si', 'sí', 's', 'yes', 'y']:
            config.github_access_token = None
            config.is_active = False
            config.updated_at = datetime.utcnow()
            db.session.commit()
            print("\n✓ Configuración reseteada exitosamente.")
            print("  - Token limpiado")
            print("  - Marcada como inactiva")
            print("\nPuedes reconfigurarla desde el panel web.")
        else:
            print("\nOperación cancelada.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        instance = sys.argv[1]
        if instance == '--reset':
            if len(sys.argv) > 2:
                reset_config(sys.argv[2])
            else:
                print("Uso: python3 clean-github-db.py --reset [instance_name]")
        else:
            clean_github_config(instance)
    else:
        clean_github_config()
