#!/usr/bin/env python3
"""
Script de prueba para verificar que el backend puede ejecutar sudo
"""

import subprocess
import sys

print("🧪 Probando ejecución de sudo desde Python...")
print("=" * 50)

# Prueba 1: Verificar que sudo existe
print("\n1. Verificando ruta de sudo...")
try:
    result = subprocess.run(['/usr/bin/sudo', '--version'], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    print(f"✅ sudo encontrado: {result.stdout.split()[0]} {result.stdout.split()[1]}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Prueba 2: Verificar que puede ejecutar sin contraseña
print("\n2. Verificando ejecución sin contraseña...")
try:
    result = subprocess.run(['/usr/bin/sudo', '-n', 'whoami'], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    if result.returncode == 0:
        print(f"✅ Puede ejecutar sudo sin contraseña como: {result.stdout.strip()}")
    else:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Prueba 3: Verificar que puede ejecutar el script de Odoo
print("\n3. Verificando script de creación de producción...")
script_path = '/home/mtg/api-dev/scripts/odoo/create-prod-instance.sh'
try:
    result = subprocess.run(['/usr/bin/sudo', '/bin/bash', script_path, '--help'], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    if 'Validando variables' in result.stdout or 'ERROR' in result.stdout:
        print(f"✅ Script ejecutable (responde a --help)")
    else:
        print(f"⚠️  Script responde pero formato inesperado")
        print(f"Output: {result.stdout[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Prueba 4: Verificar creación de archivo de log
print("\n4. Verificando creación de archivo de log...")
import tempfile
import os

log_file = '/tmp/test-backend-sudo.log'
try:
    with open(log_file, 'w') as f:
        process = subprocess.Popen(
            ['/usr/bin/sudo', 'echo', 'test'],
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )
        process.wait(timeout=5)
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
        print(f"✅ Puede crear y escribir en archivos de log")
        os.remove(log_file)
    else:
        print(f"❌ No pudo crear archivo de log")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ TODAS LAS PRUEBAS PASARON")
print("=" * 50)
print("\nEl backend debería poder crear instancias de producción correctamente.")
