#!/usr/bin/env python3
"""
Migration: Add webhook and auto-deploy fields to GitHubConfig
Date: 2025-11-12
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def migrate():
    """Agrega campos de webhook y auto-deploy al modelo GitHubConfig"""
    app = create_app()
    
    with app.app_context():
        # Usar SQL directo para agregar columnas
        try:
            # Agregar columnas nuevas
            db.session.execute(db.text("""
                ALTER TABLE github_configs 
                ADD COLUMN IF NOT EXISTS instance_type VARCHAR(20) DEFAULT 'development'
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE github_configs 
                ADD COLUMN IF NOT EXISTS auto_deploy BOOLEAN DEFAULT FALSE
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE github_configs 
                ADD COLUMN IF NOT EXISTS webhook_secret VARCHAR(100)
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE github_configs 
                ADD COLUMN IF NOT EXISTS update_modules_on_deploy BOOLEAN DEFAULT FALSE
            """))
            
            db.session.execute(db.text("""
                ALTER TABLE github_configs 
                ADD COLUMN IF NOT EXISTS last_deploy_at TIMESTAMP
            """))
            
            db.session.commit()
            
            print("✅ Migración completada exitosamente")
            print("   - instance_type agregado")
            print("   - auto_deploy agregado")
            print("   - webhook_secret agregado")
            print("   - update_modules_on_deploy agregado")
            print("   - last_deploy_at agregado")
            
            # Actualizar instancias existentes
            from models import GitHubConfig
            configs = GitHubConfig.query.all()
            
            for config in configs:
                # Detectar tipo de instancia
                if config.instance_name.startswith('dev-'):
                    config.instance_type = 'development'
                    # Usar nombre de instancia como rama para dev
                    if config.repo_branch == 'main':
                        config.repo_branch = config.instance_name
                else:
                    config.instance_type = 'production'
                    # Asegurar que producción use main
                    config.repo_branch = 'main'
            
            db.session.commit()
            print(f"\n✅ {len(configs)} configuraciones actualizadas")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en migración: {e}")
            raise

if __name__ == '__main__':
    migrate()
