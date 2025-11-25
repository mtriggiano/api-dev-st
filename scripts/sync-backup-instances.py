#!/usr/bin/env python3

"""
Script para sincronizar instancias de producción con el sistema de backups V2
Lee las instancias activas y crea sus directorios de backup si no existen
"""

import os
import json
from datetime import datetime

BACKUP_INSTANCES_DIR = "/home/mtg/backups/instances"
PROD_INSTANCES_FILE = "/home/mtg/api-dev/data/prod-instances.txt"

def main():
    print("=== Sincronizando instancias de producción con Backups V2 ===")
    
    # Crear directorio base si no existe
    os.makedirs(BACKUP_INSTANCES_DIR, exist_ok=True)
    
    count = 0
    
    # Leer instancias activas
    if not os.path.exists(PROD_INSTANCES_FILE):
        print(f"⚠️  Advertencia: No se encontró {PROD_INSTANCES_FILE}")
        return
    
    with open(PROD_INSTANCES_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Saltar líneas vacías
            if not line:
                continue
            
            # Extraer nombre de instancia (primera parte antes del |)
            parts = line.split('|')
            instance_name = parts[0].strip()
            
            if not instance_name:
                continue
            
            # Crear directorio de la instancia si no existe
            instance_dir = os.path.join(BACKUP_INSTANCES_DIR, instance_name)
            config_file = os.path.join(instance_dir, 'config.json')
            
            if not os.path.exists(instance_dir):
                print(f"📁 Creando directorio para: {instance_name}")
                os.makedirs(instance_dir, exist_ok=True)
                
                # Crear configuración por defecto
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                config = {
                    "instance_name": instance_name,
                    "auto_backup_enabled": False,
                    "schedule": "0 3 * * *",
                    "retention_days": 7,
                    "priority": "medium",
                    "last_backup": None,
                    "last_backup_status": None,
                    "last_backup_size": 0,
                    "backup_count": 0,
                    "total_size": 0,
                    "created_at": timestamp,
                    "updated_at": timestamp
                }
                
                with open(config_file, 'w') as cf:
                    json.dump(config, cf, indent=2)
                
                count += 1
            else:
                print(f"✓ {instance_name} ya existe")
    
    print()
    print("=== Sincronización completada ===")
    print(f"Instancias nuevas creadas: {count}")
    print(f"Directorio de backups: {BACKUP_INSTANCES_DIR}")
    print()
    print("Ahora puedes ver todas las instancias en Backups V2")

if __name__ == "__main__":
    main()
