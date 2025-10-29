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
                    
                    # Extraer información con regex
                    port_match = re.search(r'Puerto:\s*(\d+)', content)
                    if port_match:
                        info['port'] = int(port_match.group(1))
                    
                    domain_match = re.search(r'Dominio:\s*https?://([^\s]+)', content)
                    if domain_match:
                        info['domain'] = domain_match.group(1)
                    
                    db_match = re.search(r'Base de datos:\s*([^\s]+)', content)
                    if db_match:
                        info['database'] = db_match.group(1)
                    
                    service_match = re.search(r'Servicio systemd:\s*([^\s]+)', content)
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
    
    def create_dev_instance(self, name):
        """Crea una nueva instancia de desarrollo"""
        self._init_paths()
        script_path = os.path.join(self.scripts_path, 'create-dev-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de creación no encontrado'}
        
        try:
            # Ejecutar script en background desacoplado del proceso padre
            cmd = f"echo 's' | /bin/bash {script_path} {name} > /tmp/odoo-create-dev-{name}.log 2>&1 &"
            logger.info(f"Executing command: {cmd}")
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"Process started for instance {name}")
            
            return {
                'success': True,
                'message': f'Creación de instancia {name} iniciada. Ver logs: /tmp/odoo-create-dev-{name}.log',
                'log_file': f'/tmp/odoo-create-dev-{name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_instance(self, instance_name):
        """Elimina una instancia de desarrollo"""
        self._init_paths()
        script_path = os.path.join(self.scripts_path, 'remove-dev-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de eliminación no encontrado'}
        
        try:
            # Ejecutar script con confirmación automática
            process = subprocess.Popen(
                ['/bin/bash', script_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Enviar nombre de instancia y confirmación
            # El script espera el nombre sin "dev-" y luego BORRAR con el nombre completo
            name_without_prefix = instance_name.replace('dev-', '')
            stdout, stderr = process.communicate(
                input=f"{name_without_prefix}\nBORRAR{instance_name}\n",
                timeout=60
            )
            
            if process.returncode == 0:
                return {'success': True, 'message': f'Instancia {instance_name} eliminada', 'output': stdout}
            else:
                return {'success': False, 'error': stderr or stdout}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_instance_db(self, instance_name):
        """Actualiza la base de datos de una instancia de desarrollo"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'update-db.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script update-db.sh no encontrado'}
        
        try:
            # Ejecutar script en background con log
            cmd = f"echo 's' | /bin/bash {script_path} > /tmp/odoo-update-db-{instance_name}.log 2>&1 &"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=instance_path
            )
            
            return {
                'success': True,
                'message': f'Actualización de BD iniciada. Ver logs: /tmp/odoo-update-db-{instance_name}.log',
                'log_file': f'/tmp/odoo-update-db-{instance_name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_instance_files(self, instance_name):
        """Actualiza los archivos de una instancia de desarrollo"""
        self._init_paths()
        instance_path = os.path.join(self.dev_root, instance_name)
        script_path = os.path.join(instance_path, 'update-files.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script update-files.sh no encontrado'}
        
        try:
            # Ejecutar script en background con log
            cmd = f"echo 's' | /bin/bash {script_path} > /tmp/odoo-update-files-{instance_name}.log 2>&1 &"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=instance_path
            )
            
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
            return {'success': False, 'error': 'Script sync-filestore.sh no encontrado'}
        
        try:
            # Ejecutar script en background con log
            cmd = f"echo 's' | /bin/bash {script_path} > /tmp/odoo-sync-filestore-{instance_name}.log 2>&1 &"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=instance_path
            )
            
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
            return {'success': False, 'error': 'Script regenerate-assets.sh no encontrado'}
        
        try:
            # Ejecutar script en background con log
            cmd = f"echo 's' | /bin/bash {script_path} > /tmp/odoo-regenerate-assets-{instance_name}.log 2>&1 &"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=instance_path
            )
            
            return {
                'success': True,
                'message': f'Regeneración de assets iniciada. Ver logs: /tmp/odoo-regenerate-assets-{instance_name}.log',
                'log_file': f'/tmp/odoo-regenerate-assets-{instance_name}.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
