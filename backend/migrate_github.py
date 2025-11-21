#!/usr/bin/env python3
"""
Script de migración para agregar la tabla github_configs
Ejecutar: python3 migrate_github.py
"""

from app import create_app, init_db
from models import db

def migrate():
    """Crea las nuevas tablas en la base de datos"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Creando tabla github_configs...")
        
        try:
            # Crear todas las tablas (solo crea las que no existen)
            db.create_all()
            print("✅ Tabla github_configs creada exitosamente")
            print("✅ Migración completada")
            
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("=" * 60)
    print("MIGRACIÓN: Integración GitHub")
    print("=" * 60)
    
    if migrate():
        print("\n✅ La base de datos está lista para usar la integración GitHub")
        print("\n📚 Próximos pasos:")
        print("1. Reiniciar el servicio: sudo systemctl restart server-panel-api")
        print("2. Leer la documentación: cat /home/mtg/api-dev/GITHUB_INTEGRATION.md")
        print("3. Crear un Personal Access Token en GitHub")
        print("4. Vincular tu cuenta desde el frontend o API")
    else:
        print("\n❌ La migración falló. Revisa los errores arriba.")
