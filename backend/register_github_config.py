#!/usr/bin/env python3
"""
Script para registrar una configuración de GitHub manualmente en la base de datos
"""
import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, GitHubConfig
from datetime import datetime

def register_config():
    app = create_app()
    with app.app_context():
        # Buscar el usuario admin (o el primer usuario)
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()
        
        if not user:
            print("❌ No se encontró ningún usuario en la base de datos")
            return False
        
        # Datos de la configuración - REEMPLAZAR CON TUS VALORES
        instance_name = 'dev-NOMBRE'  # Nombre de tu instancia
        github_token = 'ghp_TU_TOKEN_AQUI'  # Tu token de GitHub
        repo_owner = 'tu-usuario'  # Tu usuario de GitHub
        repo_name = 'tu-repositorio'  # Nombre del repositorio
        repo_branch = 'dev-NOMBRE'  # Rama a usar
        local_path = '/home/go/apps/develop/odoo/dev-NOMBRE/custom_addons'
        
        # Verificar si ya existe una configuración
        existing_config = GitHubConfig.query.filter_by(
            user_id=user.id,
            instance_name=instance_name
        ).first()
        
        if existing_config:
            print(f"⚠️  Ya existe una configuración para {instance_name}")
            print(f"   Actualizando...")
            existing_config.github_username = repo_owner
            existing_config.github_access_token = github_token
            existing_config.repo_owner = repo_owner
            existing_config.repo_name = repo_name
            existing_config.repo_branch = repo_branch
            existing_config.local_path = local_path
            existing_config.is_active = True
            existing_config.updated_at = datetime.utcnow()
        else:
            print(f"✅ Creando nueva configuración para {instance_name}")
            config = GitHubConfig(
                user_id=user.id,
                instance_name=instance_name,
                github_username=repo_owner,
                github_access_token=github_token,
                repo_owner=repo_owner,
                repo_name=repo_name,
                repo_branch=repo_branch,
                local_path=local_path,
                is_active=True
            )
            db.session.add(config)
        
        db.session.commit()
        
        print("\n✅ Configuración registrada exitosamente:")
        print(f"   Usuario: {user.username}")
        print(f"   Instancia: {instance_name}")
        print(f"   Repositorio: {repo_owner}/{repo_name}")
        print(f"   Rama: {repo_branch}")
        print(f"   Ruta local: {local_path}")
        
        return True

if __name__ == '__main__':
    success = register_config()
    sys.exit(0 if success else 1)
