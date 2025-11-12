import os
import subprocess
import logging
from typing import Dict
from flask import current_app

logger = logging.getLogger(__name__)

class DeployManager:
    """Gestor de despliegues automáticos desde GitHub"""
    
    def __init__(self):
        self.dev_root = None
    
    def _init_paths(self):
        """Inicializa las rutas desde la configuración"""
        if not self.dev_root:
            self.dev_root = current_app.config.get('DEV_ROOT', '/home/go/apps')
    
    def _run_command(self, command: list, cwd: str) -> Dict:
        """Ejecuta un comando y retorna el resultado"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos max
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Comando excedió el tiempo límite (5 minutos)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def pull_changes(self, local_path: str, branch: str, token: str = None) -> Dict:
        """Hace git pull de los cambios"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Configurar token si se proporciona
        original_url = None
        if token:
            remote_result = self._run_command(['/usr/bin/git', 'remote', 'get-url', 'origin'], local_path)
            if remote_result['success'] and remote_result['stdout'].startswith('https://'):
                original_url = remote_result['stdout']
                auth_url = original_url.replace('https://', f'https://{token}@')
                self._run_command(['/usr/bin/git', 'remote', 'set-url', 'origin', auth_url], local_path)
        
        # Pull
        pull_result = self._run_command(['/usr/bin/git', 'pull', 'origin', branch], local_path)
        
        # Restaurar URL original
        if token and original_url:
            self._run_command(['/usr/bin/git', 'remote', 'set-url', 'origin', original_url], local_path)
        
        if pull_result['success']:
            return {
                'success': True,
                'message': 'Pull exitoso',
                'output': pull_result['stdout']
            }
        else:
            return {
                'success': False,
                'error': f'Error al hacer pull: {pull_result.get("stderr")}',
                'output': pull_result.get('stdout')
            }
    
    def update_odoo_modules(self, instance_name: str, modules: list = None) -> Dict:
        """Actualiza módulos de Odoo"""
        self._init_paths()
        
        # Determinar si es producción o desarrollo
        if instance_name.startswith('dev-'):
            instance_path = os.path.join(self.dev_root, 'develop', 'odoo', instance_name)
            service_name = f'odoo19e-{instance_name}'
        else:
            # Para producción, usar /home/go/apps/production
            instance_path = f'/home/go/apps/production/odoo/{instance_name}'
            service_name = f'odoo19e-{instance_name}'
        
        # Verificar que existe el servicio
        check_service = self._run_command(['/usr/bin/sudo', '/usr/bin/systemctl', 'is-active', service_name], '/')
        logger.info(f"Check service result: {check_service}")
        if not check_service['success']:
            return {
                'success': False,
                'error': f'Servicio {service_name} no está activo. Check result: {check_service}'
            }
        
        # Construir comando de actualización
        odoo_bin = os.path.join(instance_path, 'odoo-server', 'odoo-bin')
        config_file = os.path.join(instance_path, 'odoo.conf')
        
        if not os.path.exists(odoo_bin):
            return {
                'success': False,
                'error': f'odoo-bin no encontrado en {odoo_bin}'
            }
        
        # Si no se especifican módulos, actualizar todos los custom addons
        if not modules:
            modules_str = 'all'
        else:
            modules_str = ','.join(modules)
        
        # Detener servicio
        logger.info(f"Deteniendo servicio {service_name}")
        stop_result = self._run_command(['/usr/bin/sudo', '/usr/bin/systemctl', 'stop', service_name], '/')
        
        if not stop_result['success']:
            return {
                'success': False,
                'error': f'Error al detener servicio: {stop_result.get("stderr")}'
            }
        
        # Actualizar módulos
        logger.info(f"Actualizando módulos: {modules_str}")
        update_cmd = [
            '/usr/bin/sudo', '-u', 'go',
            odoo_bin,
            '-c', config_file,
            '-u', modules_str if modules_str != 'all' else 'base',
            '--stop-after-init'
        ]
        
        update_result = self._run_command(update_cmd, instance_path)
        
        # Reiniciar servicio
        logger.info(f"Reiniciando servicio {service_name}")
        start_result = self._run_command(['/usr/bin/sudo', '/usr/bin/systemctl', 'start', service_name], '/')
        
        if not start_result['success']:
            return {
                'success': False,
                'error': f'Error al reiniciar servicio: {start_result.get("stderr")}',
                'update_output': update_result.get('stdout')
            }
        
        # Verificar que el servicio está activo
        check_result = self._run_command(['/usr/bin/sudo', '/usr/bin/systemctl', 'is-active', service_name], '/')
        
        return {
            'success': check_result['success'],
            'message': f'Módulos actualizados y servicio reiniciado' if check_result['success'] else 'Error al verificar servicio',
            'update_output': update_result.get('stdout'),
            'service_status': check_result.get('stdout')
        }
    
    def auto_deploy(self, config, commit_info: Dict = None) -> Dict:
        """Ejecuta un despliegue automático completo"""
        results = {
            'pull': None,
            'update_modules': None,
            'success': False
        }
        
        try:
            # 1. Pull de cambios
            logger.info(f"Iniciando auto-deploy para {config.instance_name}")
            pull_result = self.pull_changes(
                config.local_path,
                config.repo_branch,
                config.github_access_token
            )
            results['pull'] = pull_result
            
            if not pull_result['success']:
                return {
                    **results,
                    'error': 'Error en git pull',
                    'success': False
                }
            
            # 2. Actualizar módulos si está configurado
            if config.update_modules_on_deploy:
                logger.info(f"Actualizando módulos de Odoo para {config.instance_name}")
                update_result = self.update_odoo_modules(config.instance_name)
                results['update_modules'] = update_result
                
                if not update_result['success']:
                    return {
                        **results,
                        'error': 'Error al actualizar módulos',
                        'success': False
                    }
            
            results['success'] = True
            results['message'] = 'Deploy completado exitosamente'
            
            if commit_info:
                results['commit'] = commit_info
            
            return results
            
        except Exception as e:
            logger.error(f"Error en auto-deploy: {e}")
            return {
                **results,
                'error': str(e),
                'success': False
            }

# Instancia global
deploy_manager = DeployManager()
