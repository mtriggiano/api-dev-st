import os
import subprocess
import re
import sys
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

class InstanceManager:
    """Gestor de instancias Odoo"""
    
    def __init__(self):
        self.prod_root = None
        self.dev_root = None
        self.scripts_path = None
        self.puertos_file = None
        self.dev_instances_file = None
    
    def _init_paths(self):
        """Inicializa las rutas desde la configuración"""
        if not self.prod_root:
            self.prod_root = current_app.config['PROD_ROOT']
            self.dev_root = current_app.config['DEV_ROOT']
            self.scripts_path = current_app.config['SCRIPTS_PATH']
            self.puertos_file = current_app.config['PUERTOS_FILE']
            self.dev_instances_file = current_app.config['DEV_INSTANCES_FILE']
    
    def list_instances(self):
        """Lista todas las instancias (producción y desarrollo)"""
        self._init_paths()
        instances = []
        
        # Instancias de producción
        if os.path.exists(self.prod_root):
            for name in os.listdir(self.prod_root):
                path = os.path.join(self.prod_root, name)
                if os.path.isdir(path):
                    info = self._get_instance_info(name, path, 'production')
                    instances.append(info)
        
        # Instancias de desarrollo
        if os.path.exists(self.dev_root):
            for name in os.listdir(self.dev_root):
                path = os.path.join(self.dev_root, name)
                if os.path.isdir(path):
                    info = self._get_instance_info(name, path, 'development')
                    instances.append(info)
        
        return instances
    
    def list_production_instances(self):
        """Lista solo las instancias de producción válidas para clonar"""
        self._init_paths()
        instances = []
        
        if os.path.exists(self.prod_root):
            for name in os.listdir(self.prod_root):
                path = os.path.join(self.prod_root, name)
                # Filtrar solo directorios válidos con odoo.conf
                if os.path.isdir(path) and os.path.exists(os.path.join(path, 'odoo.conf')):
                    # Excluir directorios especiales
                    if name not in ['temp', 'backups']:
                        info = self._get_instance_info(name, path, 'production')
                        instances.append(info)
        
        return instances
    
    def _get_instance_info(self, name, path, env_type):
        """Obtiene información de una instancia"""
        info = {
            'name': name,
            'type': env_type,
            'path': path,
            'status': 'unknown',
            'port': None,
            'domain': None,
            'database': None,
            'service': None
        }
        
        # Leer archivo info-instancia.txt si existe
        info_file = os.path.join(path, 'info-instancia.txt')
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extraer información con regex (soporta formato con y sin emojis)
                    port_match = re.search(r'Puerto(?:\s+HTTP)?:\s*(\d+)', content)
                    if port_match:
                        info['port'] = int(port_match.group(1))
                    
                    domain_match = re.search(r'Dominio:\s*https?://([^\s]+)', content)
                    if domain_match:
                        info['domain'] = domain_match.group(1)
                    
                    db_match = re.search(r'Base de datos:\s*([^\s]+)', content)
                    if db_match:
                        info['database'] = db_match.group(1)
                    
                    # Buscar servicio con varios formatos posibles
                    service_match = re.search(r'(?:Servicio(?:\s+systemd)?|🧩\s+Servicio):\s*([^\s]+)', content)
                    if service_match:
                        info['service'] = service_match.group(1)
            except Exception as e:
                print(f"Error leyendo info de {name}: {e}")
        
        # Verificar estado del servicio
        if info['service']:
            try:
                info['status'] = self._get_service_status(info['service'])
                print(f"Service {info['service']} status: {info['status']}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"Error getting status for {info['service']}: {e}", file=sys.stderr, flush=True)
                info['status'] = 'unknown'
        
        return info
    
    def _get_service_status(self, service_name):
        """Obtiene el estado de un servicio systemd"""
        try:
            result = subprocess.run(
                ['/usr/bin/systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            status = result.stdout.strip()
            logger.info(f"Service check: {service_name} -> stdout='{status}', returncode={result.returncode}")
            
            # Retornar el estado tal como lo devuelve systemctl
            if status == 'active':
                return 'active'
            elif status == 'inactive':
                return 'inactive'
            elif status == 'failed':
                return 'inactive'
            else:
                logger.warning(f"Unknown status '{status}' for service {service_name}")
                return 'unknown'
        except Exception as e:
            logger.error(f"Error checking service status for {service_name}: {e}")
            return 'unknown'
    
    def get_instance_status(self, instance_name):
        """Obtiene el estado detallado de una instancia"""
        instances = self.list_instances()
        instance = next((i for i in instances if i['name'] == instance_name), None)
        
        if not instance:
            return None
        
        # Información adicional del servicio
        if instance['service']:
            try:
                result = subprocess.run(
                    ['/usr/bin/systemctl', 'status', instance['service']],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                instance['service_details'] = result.stdout
            except Exception as e:
                instance['service_details'] = f"Error: {str(e)}"
        
        return instance

    def _extract_conf_value(self, conf_content: str, key: str):
        pattern = rf'^\s*{re.escape(key)}\s*=\s*(.+?)\s*$'
        match = re.search(pattern, conf_content, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _infer_dev_context(self, instance_name: str, instance_path: str):
        conf_path = os.path.join(instance_path, 'odoo.conf')
        if not os.path.exists(conf_path):
            return None

        try:
            with open(conf_path, 'r', encoding='utf-8') as f:
                conf_content = f.read()
        except Exception:
            return None

        dev_db = self._extract_conf_value(conf_content, 'db_name')
        if not dev_db:
            return None

        prefix = f'{instance_name}-'
        if dev_db.startswith(prefix):
            prod_db = dev_db[len(prefix):]
        else:
            match = re.search(r'(prod-[A-Za-z0-9_-]+)$', dev_db)
            prod_db = match.group(1) if match else None

        if not prod_db:
            return None

        return {
            'instance_name': instance_name,
            'instance_path': instance_path,
            'prod_db': prod_db,
            'dev_db': dev_db,
            'prod_dir': os.path.join(self.prod_root, prod_db),
            'scripts_path': self.scripts_path,
        }

    def _ensure_dev_action_scripts(self, instance_name: str, instance_path: str):
        """Regenera scripts auxiliares si faltan en una instancia dev."""
        self._init_paths()
        context = self._infer_dev_context(instance_name, instance_path)
        if not context:
            return False, 'No se pudo inferir contexto de la instancia desde odoo.conf'

        update_db_template = """#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para actualizar la BD de desarrollo desde producción

PROD_DB="__PROD_DB__"
DEV_DB="__DEV_DB__"
INSTANCE_NAME="__INSTANCE_NAME__"

echo "🔄 Actualizando base de datos de desarrollo desde producción..."
echo "   Producción: $PROD_DB"
echo "   Desarrollo: $DEV_DB"

if [ -t 0 ]; then
  read -p "Confirmar actualización (s/n): " CONFIRM
else
  read CONFIRM
fi
if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

echo "⏹️  Deteniendo servicio Odoo..."
sudo systemctl stop "odoo19e-$INSTANCE_NAME"

echo "🗄️  Eliminando BD de desarrollo actual..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DEV_DB';" >/dev/null 2>&1
sudo -u postgres dropdb "$DEV_DB" 2>/dev/null

echo "📦 Creando dump de producción..."
sudo -u postgres pg_dump "$PROD_DB" > "/tmp/${DEV_DB}_dump.sql"

echo "🔄 Restaurando en desarrollo..."
sudo -u postgres createdb "$DEV_DB" -O "mtg" --encoding='UTF8'
sudo -u postgres psql -d "$DEV_DB" < "/tmp/${DEV_DB}_dump.sql"
rm -f "/tmp/${DEV_DB}_dump.sql"

echo "🔐 Configurando permisos..."
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL ON SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mtg;" > /dev/null
sudo -u postgres psql -d "$DEV_DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mtg;" > /dev/null

echo "📁 Sincronizando filestore..."
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
PROD_FILESTORE="$FILESTORE_BASE/$PROD_DB"
DEV_FILESTORE="$FILESTORE_BASE/$DEV_DB"
if [[ -d "$PROD_FILESTORE" ]]; then
  mkdir -p "$DEV_FILESTORE"
  rsync -a --delete "$PROD_FILESTORE/" "$DEV_FILESTORE/"
  echo "✅ Filestore sincronizado ($(find $DEV_FILESTORE -type f | wc -l) archivos)"
fi

echo "🎨 Regenerando assets..."
cd "__BASE_DIR__"
source venv/bin/activate
./venv/bin/python3 ./odoo-server/odoo-bin -c ./odoo.conf --update=all --stop-after-init

echo "🛡️  Aplicando neutralización post-update..."
"__SCRIPTS_PATH__/odoo/neutralize-database-sql.sh" "$DEV_DB"

echo "▶️  Iniciando servicio Odoo..."
sudo systemctl start "odoo19e-$INSTANCE_NAME"

echo "✅ Base de datos actualizada correctamente."
"""

        update_files_template = """#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para actualizar archivos de desarrollo desde producción

PROD_DIR="__PROD_DIR__"
DEV_DIR="__BASE_DIR__"
INSTANCE_NAME="__INSTANCE_NAME__"

echo "🔄 Actualizando archivos desde producción..."
echo "   Producción: $PROD_DIR"
echo "   Desarrollo: $DEV_DIR"

if [ -t 0 ]; then
  read -p "Confirmar actualización (s/n): " CONFIRM
else
  read CONFIRM
fi
if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

echo "⏹️  Deteniendo servicio Odoo..."
sudo systemctl stop "odoo19e-$INSTANCE_NAME"

echo "💾 Haciendo backup de custom_addons..."
if [[ -d "$DEV_DIR/custom_addons" ]]; then
  cp -r "$DEV_DIR/custom_addons" "$DEV_DIR/custom_addons.backup"
fi

echo "🗑️  Eliminando odoo-server actual..."
rm -rf "$DEV_DIR/odoo-server"

echo "📦 Copiando archivos desde producción..."
mkdir -p "$DEV_DIR/odoo-server"
cp -r "$PROD_DIR/odoo-server/"* "$DEV_DIR/odoo-server/"

echo "🔄 Restaurando custom_addons..."
if [[ -d "$DEV_DIR/custom_addons.backup" ]]; then
  rm -rf "$DEV_DIR/custom_addons"
  mv "$DEV_DIR/custom_addons.backup" "$DEV_DIR/custom_addons"
fi

echo "🐍 Actualizando dependencias Python..."
source "$DEV_DIR/venv/bin/activate"
pip install --upgrade pip wheel
pip install -r "$DEV_DIR/odoo-server/requirements.txt"
pip install phonenumbers gevent greenlet

echo "▶️  Iniciando servicio Odoo..."
sudo systemctl start "odoo19e-$INSTANCE_NAME"

echo "✅ Archivos actualizados correctamente."
"""

        sync_filestore_template = """#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para sincronizar filestore desde producción

PROD_DB="__PROD_DB__"
DEV_DB="__DEV_DB__"
INSTANCE_NAME="__INSTANCE_NAME__"

echo "📁 Sincronizando filestore desde producción..."
echo "   Producción: $PROD_DB"
echo "   Desarrollo: $DEV_DB"

if [ -t 0 ]; then
  read -p "Confirmar sincronización (s/n): " CONFIRM
else
  read CONFIRM
fi
if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

echo "⏹️  Deteniendo servicio Odoo..."
sudo systemctl stop "odoo19e-$INSTANCE_NAME"

echo "📁 Sincronizando filestore..."
FILESTORE_BASE="/home/mtg/.local/share/Odoo/filestore"
PROD_FILESTORE="$FILESTORE_BASE/$PROD_DB"
DEV_FILESTORE="$FILESTORE_BASE/$DEV_DB"

if [[ -d "$PROD_FILESTORE" ]]; then
  mkdir -p "$DEV_FILESTORE"
  rsync -a --delete "$PROD_FILESTORE/" "$DEV_FILESTORE/"
  FILE_COUNT=$(find "$DEV_FILESTORE" -type f | wc -l)
  echo "✅ Filestore sincronizado ($FILE_COUNT archivos)"
else
  echo "⚠️  No se encontró filestore de producción en $PROD_FILESTORE"
fi

echo "▶️  Iniciando servicio Odoo..."
sudo systemctl start "odoo19e-$INSTANCE_NAME"

echo "✅ Filestore sincronizado correctamente."
"""

        regenerate_assets_template = """#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Script para regenerar assets de Odoo

INSTANCE_NAME="__INSTANCE_NAME__"
BASE_DIR="__BASE_DIR__"

echo "🎨 Regenerando assets de Odoo..."
echo "   Instancia: $INSTANCE_NAME"

if [ -t 0 ]; then
  read -p "Confirmar regeneración (s/n): " CONFIRM
else
  read CONFIRM
fi
if [[ "$CONFIRM" != "s" ]] && [[ "$CONFIRM" != "S" ]]; then
  echo "❌ Cancelado."
  exit 1
fi

echo "⏹️  Deteniendo servicio Odoo..."
sudo systemctl stop "odoo19e-$INSTANCE_NAME"
sleep 5

echo "🎨 Regenerando assets..."
cd "$BASE_DIR"
source venv/bin/activate

TEMP_LOG="/tmp/odoo-regenerate-$INSTANCE_NAME.log"
./venv/bin/python3 ./odoo-server/odoo-bin -c ./odoo.conf --update=all --stop-after-init > "$TEMP_LOG" 2>&1 &
ODOO_PID=$!

echo "   Procesando (esto puede tardar 1-2 minutos)..."
while kill -0 $ODOO_PID 2>/dev/null; do
  sleep 2
  echo -n "."
done
echo ""

wait $ODOO_PID
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ Regeneración completada exitosamente"
else
  echo "⚠️  Proceso terminó con código: $EXIT_CODE"
  echo "   Ver log completo en: $TEMP_LOG"
fi

echo "▶️  Iniciando servicio Odoo..."
sudo systemctl start "odoo19e-$INSTANCE_NAME"

echo "✅ Assets regenerados correctamente"
"""

        replacements = {
            '__PROD_DB__': context['prod_db'],
            '__DEV_DB__': context['dev_db'],
            '__INSTANCE_NAME__': context['instance_name'],
            '__BASE_DIR__': context['instance_path'],
            '__PROD_DIR__': context['prod_dir'],
            '__SCRIPTS_PATH__': context['scripts_path'],
        }

        scripts = {
            'update-db.sh': update_db_template,
            'update-files.sh': update_files_template,
            'sync-filestore.sh': sync_filestore_template,
            'regenerate-assets.sh': regenerate_assets_template,
        }

        created_scripts = []
        for script_name, template in scripts.items():
            script_path = os.path.join(instance_path, script_name)
            if os.path.exists(script_path):
                continue

            script_content = template
            for source, target in replacements.items():
                script_content = script_content.replace(source, target)

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)
            created_scripts.append(script_name)

        return True, created_scripts
    
    def create_dev_instance(
        self,
        name: str,
        source_instance: str = None,
        neutralize: bool = True,
        git_branch: str = '',
        system_username: str = '',
        system_instance_accesses=None,
    ):
        """
        Crea una nueva instancia de desarrollo clonando desde producción
        Args:
            name: Nombre de la instancia (sin prefijo dev-)
            source_instance: Instancia de producción a clonar (opcional, usa default del .env si no se especifica)
            neutralize: Si True, neutraliza la base de datos (elimina licencia, desactiva crons/correos)
            git_branch: Rama Git por defecto para esta instancia (opcional)
        """
        self._init_paths()
        script_path = os.path.join(self.scripts_path, 'odoo/create-dev-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de creación no encontrado'}
        
        try:
            # Preparar argumentos del script
            script_args = ['/bin/bash', script_path, name]
            
            # Si se especificó una instancia de producción, agregarla como segundo argumento
            if source_instance:
                script_args.append(source_instance)
            else:
                script_args.append('')  # Placeholder para mantener posiciones
            
            # Agregar opción de neutralización como tercer argumento
            neutralize_arg = 'neutralize' if neutralize else 'no-neutralize'
            script_args.append(neutralize_arg)
            
            # Agregar auto-confirm como cuarto argumento (modo no interactivo)
            script_args.append('true')
            
            # Agregar rama Git como quinto argumento (opcional)
            script_args.append(git_branch if git_branch else '')

            # Agregar usuario Linux y asignaciones para ACL (opcional)
            script_args.append(system_username if system_username else '')
            system_access_arg = ','.join(system_instance_accesses or [])
            script_args.append(system_access_arg)
            
            # El nombre de la instancia completa incluye el prefijo "dev-"
            instance_name = f'dev-{name}'
            log_file_path = f'/tmp/odoo-create-{instance_name}.log'
            
            # Ejecutar script en background desacoplado del proceso padre
            with open(log_file_path, 'w') as log_file:
                process = subprocess.Popen(
                    script_args,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    text=True,
                    bufsize=1
                )
            logger.info(f"Process started for dev instance {instance_name} from source {source_instance or 'default'} (neutralize={neutralize}, git_branch={git_branch or 'default'})")
            
            return {
                'success': True,
                'message': f'Creación de instancia {instance_name} iniciada. Ver logs: {log_file_path}',
                'log_file': log_file_path,
                'instance_name': instance_name,  # Devolver el nombre completo de la instancia
                'git_branch': git_branch  # Devolver la rama Git configurada
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_prod_instance(self, name, version='19', edition='enterprise', ssl_method='letsencrypt'):
        """Crea una nueva instancia de producción con subdominio obligatorio
        
        Args:
            name: Nombre de la instancia (será usado como subdominio)
            version: Versión de Odoo (19 o 18)
            edition: Edición (enterprise o community)
            ssl_method: Método SSL a usar (cloudflare, letsencrypt, http)
        
        Returns:
            dict: Resultado de la operación
        """
        self._init_paths()
        
        # Validar que el nombre no intente usar el dominio raíz
        domain_root = current_app.config.get('DOMAIN_ROOT', 'softrigx.com')
        forbidden_names = [domain_root, 'production', 'prod', 'www', 'api', 'mail', 'ftp']
        
        if name.lower() in forbidden_names:
            return {
                'success': False, 
                'error': f'Nombre prohibido. "{name}" está reservado para proteger el dominio principal.'
            }
        
        # Validar formato DNS válido
        import re
        if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', name.lower()):
            return {
                'success': False,
                'error': 'Nombre inválido. Debe contener solo letras minúsculas, números y guiones.'
            }
        
        # Validar versión y edición
        if version not in ['18', '19']:
            return {'success': False, 'error': 'Versión debe ser 18 o 19'}
        
        if edition not in ['enterprise', 'community']:
            return {'success': False, 'error': 'Edición debe ser enterprise o community'}
        
        script_path = os.path.join(self.scripts_path, 'odoo/create-prod-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de creación de producción no encontrado'}
        
        try:
            instance_name = f'prod-{name.lower()}'
            pid_file = f"/tmp/{instance_name}.pid"
            status_file = f"/tmp/{instance_name}.status"
            log_file_path = f'/tmp/odoo-create-{instance_name}.log'
            
            # Mapear método SSL a número (1=letsencrypt, 2=cloudflare, 3=http)
            ssl_map = {'letsencrypt': '1', 'cloudflare': '2', 'http': '3'}
            ssl_arg = ssl_map.get(ssl_method, '1')

            # Ejecutar script en background desacoplado del proceso padre
            # Argumentos: nombre, version, edition, ssl_method
            log_fd = os.open(log_file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            process = subprocess.Popen(
                ['/bin/bash', script_path, name, version, edition, ssl_arg],
                stdout=log_fd,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
                bufsize=1
            )
            os.close(log_fd)

            # Guardar PID y estado inicial
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            with open(status_file, 'w') as f:
                f.write("running")
            
            logger.info(f"Production instance creation started: {instance_name} (Odoo {version} {edition})")
            
            return {
                'success': True,
                'message': f'Creación de instancia de producción {instance_name} iniciada. Dominio: {name}.{domain_root} - Odoo {version} {edition}',
                'log_file': log_file_path,
                'instance_name': instance_name,
                'domain': f'{name}.{domain_root}',
                'version': version,
                'edition': edition,
                'pid': process.pid,
                'status_file': status_file
            }
        except Exception as e:
            logger.error(f"Error creating production instance: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_instance(self, instance_name):
        """Elimina una instancia de desarrollo"""
        self._init_paths()
        script_path = os.path.join(self.scripts_path, 'odoo/remove-dev-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de eliminación no encontrado'}
        
        try:
            # Ejecutar script con confirmación automática y guardar log
            with open(f'/tmp/odoo-delete-{instance_name}.log', 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Enviar nombre de instancia y confirmación
                # El script espera el nombre sin "dev-" y luego BORRAR con el nombre completo
                name_without_prefix = instance_name.replace('dev-', '')
                process.stdin.write(f"{name_without_prefix}\nBORRAR{instance_name}\n")
                process.stdin.close()
                
                # Esperar hasta 5 minutos para la eliminación
                process.wait(timeout=300)
            
            if process.returncode == 0:
                return {'success': True, 'message': f'Instancia {instance_name} eliminada', 'log_file': f'/tmp/odoo-delete-{instance_name}.log'}
            else:
                # Leer el log para ver qué falló
                with open(f'/tmp/odoo-delete-{instance_name}.log', 'r') as log_file:
                    error_log = log_file.read()
                return {'success': False, 'error': f'Error en eliminación. Ver log: /tmp/odoo-delete-{instance_name}.log', 'log': error_log}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_production_instance(self, instance_name, confirmation):
        """Elimina una instancia de producción con doble confirmación"""
        self._init_paths()
        script_path = os.path.join(self.scripts_path, 'odoo/remove-production.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de eliminación no encontrado'}
        
        # Validar confirmación
        expected_confirmation = f"BORRAR{instance_name}"
        if confirmation != expected_confirmation:
            return {'success': False, 'error': f'Confirmación incorrecta. Debes escribir exactamente: {expected_confirmation}'}
        
        try:
            # Ejecutar script con confirmación automática y guardar log
            log_path = f'/tmp/odoo-delete-prod-{instance_name}.log'
            with open(log_path, 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Enviar nombre de instancia y confirmación
                process.stdin.write(f"{instance_name}\n{expected_confirmation}\n")
                process.stdin.close()
                
                # Esperar hasta 5 minutos para la eliminación
                process.wait(timeout=300)
            
            if process.returncode == 0:
                return {'success': True, 'message': f'Instancia de producción {instance_name} eliminada correctamente', 'log_file': log_path}
            else:
                # Leer el log para ver qué falló
                with open(log_path, 'r') as log_file:
                    error_log = log_file.read()
                return {'success': False, 'error': f'Error en eliminación. Ver log: {log_path}', 'log': error_log}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'La eliminación tardó demasiado tiempo (timeout de 5 minutos)'}
        except Exception as e:
            logger.error(f"Error deleting production instance: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_instance_db(self, instance_name, neutralize=True):
        """Actualiza la base de datos de una instancia de desarrollo"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'update-db.sh')
        
        if not os.path.exists(script_path):
            ok, details = self._ensure_dev_action_scripts(instance_name, instance_path)
            if not ok or not os.path.exists(script_path):
                return {'success': False, 'error': f'Script update-db.sh no encontrado. {details}'}
            logger.info(f'Scripts regenerados para {instance_name}: {details}')
        
        try:
            # Responder automáticamente: s para continuar, s/n para neutralizar
            neutralize_answer = 's' if neutralize else 'n'
            with open(f'/tmp/odoo-update-db-{instance_name}.log', 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=instance_path,
                    text=True
                )
                # Enviar confirmación para continuar y para neutralizar
                process.stdin.write(f's\n{neutralize_answer}\n')
                process.stdin.close()
            
            neutralize_msg = " (con neutralización)" if neutralize else " (sin neutralización)"
            return {
                'success': True,
                'message': f'Actualización de BD iniciada{neutralize_msg}. Ver logs: /tmp/odoo-update-db-{instance_name}.log',
                'log_file': f'/tmp/odoo-update-db-{instance_name}.log',
                'neutralize': neutralize
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_instance_files(self, instance_name):
        """Actualiza los archivos de una instancia de desarrollo"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'update-files.sh')
        
        if not os.path.exists(script_path):
            ok, details = self._ensure_dev_action_scripts(instance_name, instance_path)
            if not ok or not os.path.exists(script_path):
                return {'success': False, 'error': f'Script update-files.sh no encontrado. {details}'}
            logger.info(f'Scripts regenerados para {instance_name}: {details}')
        
        try:
            # Ejecutar script en background con log
            with open(f'/tmp/odoo-update-files-{instance_name}.log', 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=instance_path,
                    text=True
                )
                # Enviar confirmación
                process.stdin.write('s\n')
                process.stdin.close()
            
            return {
                'success': True,
                'message': f'Actualización de archivos iniciada. Ver logs: /tmp/odoo-update-files-{instance_name}.log',
                'log_file': f'/tmp/odoo-update-files-{instance_name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_instance_logs(self, instance_name, lines=100, log_type='systemd'):
        """Obtiene los logs de una instancia según el tipo especificado"""
        instances = self.list_instances()
        instance = next((i for i in instances if i['name'] == instance_name), None)
        
        if not instance:
            return {'success': False, 'error': 'Instancia no encontrada'}
        
        try:
            if log_type == 'systemd':
                # Logs de systemd journal
                if not instance['service']:
                    return {'success': False, 'error': 'Servicio no encontrado'}
                
                result = subprocess.run(
                    ['/usr/bin/journalctl', '-u', instance['service'], '-n', str(lines), '--no-pager'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return {
                    'success': True,
                    'logs': result.stdout,
                    'lines': lines,
                    'type': 'systemd'
                }
            
            elif log_type == 'odoo':
                # Log file de Odoo
                log_file = os.path.join(instance['path'], 'odoo.log')
                if not os.path.exists(log_file):
                    return {'success': False, 'error': 'Archivo odoo.log no encontrado'}
                
                result = subprocess.run(
                    ['/usr/bin/tail', '-n', str(lines), log_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    return {'success': False, 'error': f'Error al leer log: {result.stderr}'}
                
                return {
                    'success': True,
                    'logs': result.stdout if result.stdout else 'No hay logs disponibles',
                    'lines': lines,
                    'type': 'odoo'
                }
            
            elif log_type == 'nginx-access':
                # Logs de acceso de Nginx filtrados por dominio
                if not instance['domain']:
                    return {'success': False, 'error': 'Dominio no encontrado'}
                
                result = subprocess.run(
                    f"/usr/bin/grep '{instance['domain']}' /var/log/nginx/access.log | /usr/bin/tail -n {lines}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    logs_text = result.stdout
                elif result.returncode == 1:  # grep no encontró coincidencias
                    logs_text = f'No hay logs de acceso para el dominio {instance["domain"]}'
                else:
                    logs_text = f'Error al leer logs: {result.stderr}'
                
                return {
                    'success': True,
                    'logs': logs_text,
                    'lines': lines,
                    'type': 'nginx-access'
                }
            
            elif log_type == 'nginx-error':
                # Logs de error de Nginx filtrados por dominio
                if not instance['domain']:
                    return {'success': False, 'error': 'Dominio no encontrado'}
                
                result = subprocess.run(
                    f"/usr/bin/grep '{instance['domain']}' /var/log/nginx/error.log | /usr/bin/tail -n {lines}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    logs_text = result.stdout
                elif result.returncode == 1:  # grep no encontró coincidencias
                    logs_text = f'No hay logs de error para el dominio {instance["domain"]}'
                else:
                    logs_text = f'Error al leer logs: {result.stderr}'
                
                return {
                    'success': True,
                    'logs': logs_text,
                    'lines': lines,
                    'type': 'nginx-error'
                }
            
            else:
                return {'success': False, 'error': f'Tipo de log no válido: {log_type}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restart_instance(self, instance_name):
        """Reinicia una instancia"""
        instances = self.list_instances()
        instance = next((i for i in instances if i['name'] == instance_name), None)
        
        if not instance or not instance['service']:
            return {'success': False, 'error': 'Instancia o servicio no encontrado'}
        
        try:
            subprocess.run(
                ['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', instance['service']],
                check=True,
                timeout=30
            )
            return {'success': True, 'message': f'Instancia {instance_name} reiniciada'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sync_filestore(self, instance_name):
        """Sincroniza el filestore de una instancia de desarrollo desde producción"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'sync-filestore.sh')
        
        if not os.path.exists(script_path):
            ok, details = self._ensure_dev_action_scripts(instance_name, instance_path)
            if not ok or not os.path.exists(script_path):
                return {'success': False, 'error': f'Script sync-filestore.sh no encontrado. {details}'}
            logger.info(f'Scripts regenerados para {instance_name}: {details}')
        
        try:
            # Ejecutar script en background con log
            with open(f'/tmp/odoo-sync-filestore-{instance_name}.log', 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=instance_path,
                    text=True
                )
                # Enviar confirmación
                process.stdin.write('s\n')
                process.stdin.close()
            
            return {
                'success': True,
                'message': f'Sincronización de filestore iniciada. Ver logs: /tmp/odoo-sync-filestore-{instance_name}.log',
                'log_file': f'/tmp/odoo-sync-filestore-{instance_name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def regenerate_assets(self, instance_name):
        """Regenera los assets de una instancia de desarrollo"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'regenerate-assets.sh')
        
        if not os.path.exists(script_path):
            ok, details = self._ensure_dev_action_scripts(instance_name, instance_path)
            if not ok or not os.path.exists(script_path):
                return {'success': False, 'error': f'Script regenerate-assets.sh no encontrado. {details}'}
            logger.info(f'Scripts regenerados para {instance_name}: {details}')
        
        try:
            # Ejecutar script en background con log
            with open(f'/tmp/odoo-regenerate-assets-{instance_name}.log', 'w') as log_file:
                process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    stdin=subprocess.PIPE,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    cwd=instance_path,
                    text=True
                )
                # Enviar confirmación
                process.stdin.write('s\n')
                process.stdin.close()
            
            return {
                'success': True,
                'message': f'Regeneración de assets iniciada. Ver logs: /tmp/odoo-regenerate-assets-{instance_name}.log',
                'log_file': f'/tmp/odoo-regenerate-assets-{instance_name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
