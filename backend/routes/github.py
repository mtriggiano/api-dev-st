from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, GitHubConfig, ActionLog
from services.git_manager import GitManager
from services.deploy_manager import deploy_manager
from datetime import datetime
import os
import hmac
import hashlib
import secrets
import logging

github_bp = Blueprint('github', __name__)
git_manager = GitManager()
logger = logging.getLogger(__name__)

def log_action(user_id, action, instance_name=None, details=None, status='success'):
    """Registra una acción en el log"""
    try:
        log = ActionLog(
            user_id=user_id,
            action=action,
            instance_name=instance_name,
            details=details,
            status=status,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")

@github_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verifica un token de GitHub y obtiene info del usuario"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo developers y admins pueden vincular GitHub
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('token'):
        return jsonify({'error': 'Token requerido'}), 400
    
    try:
        result = git_manager.verify_github_token(data['token'])
        
        if result['success']:
            log_action(user_id, 'verify_github_token', None, f"Usuario GitHub: {result['username']}", 'success')
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/repos', methods=['GET'])
@jwt_required()
def list_repos():
    """Lista los repositorios del usuario autenticado en GitHub"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    # Obtener token del header
    token = request.headers.get('X-GitHub-Token')
    if not token:
        return jsonify({'error': 'Token de GitHub requerido en header X-GitHub-Token'}), 400
    
    try:
        result = git_manager.list_user_repos(token)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config', methods=['GET'])
@jwt_required()
def list_configs():
    """Lista las configuraciones de GitHub del usuario"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        configs = GitHubConfig.query.filter_by(user_id=user_id, is_active=True).all()
        return jsonify({
            'configs': [config.to_dict() for config in configs],
            'count': len(configs)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config/<instance_name>', methods=['GET'])
@jwt_required()
def get_config(instance_name):
    """Obtiene la configuración de GitHub para una instancia específica"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'success': False, 'config': None}), 200
        
        return jsonify({'success': True, 'config': config.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config', methods=['POST'])
@jwt_required()
def create_config():
    """Crea o actualiza una configuración de GitHub para una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    required_fields = ['instance_name', 'github_token', 'repo_owner', 'repo_name', 'local_path']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo requerido: {field}'}), 400
    
    try:
        # Verificar que el token sea válido
        verify_result = git_manager.verify_github_token(data['github_token'])
        if not verify_result['success']:
            return jsonify({'error': 'Token de GitHub inválido'}), 400
        
        # Verificar que la ruta local exista
        local_path = data['local_path']
        if not os.path.exists(local_path):
            return jsonify({'error': f'La ruta {local_path} no existe'}), 400
        
        # Buscar configuración existente
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=data['instance_name']
        ).first()
        
        if config:
            # Actualizar existente
            config.github_username = verify_result['username']
            config.github_access_token = data['github_token']
            config.repo_owner = data['repo_owner']
            config.repo_name = data['repo_name']
            config.repo_branch = data.get('repo_branch', 'main')
            config.local_path = local_path
            config.is_active = True
            config.updated_at = datetime.utcnow()
            action = 'update_github_config'
        else:
            # Crear nueva
            config = GitHubConfig(
                user_id=user_id,
                instance_name=data['instance_name'],
                github_username=verify_result['username'],
                github_access_token=data['github_token'],
                repo_owner=data['repo_owner'],
                repo_name=data['repo_name'],
                repo_branch=data.get('repo_branch', 'main'),
                local_path=local_path,
                is_active=True
            )
            db.session.add(config)
            action = 'create_github_config'
        
        db.session.commit()
        
        # Manejar inicialización/verificación del repositorio Git
        git_dir = os.path.join(local_path, '.git')
        clone_attempted = False
        clone_result = None
        repo_url = f"https://github.com/{data['repo_owner']}/{data['repo_name']}.git"
        
        if os.path.exists(git_dir):
            # El repositorio ya existe, verificar y limpiar el remote si es necesario
            logger.info(f"Repositorio Git ya existe en {local_path}, verificando configuración...")
            
            # Obtener URL actual del remote
            remote_check = git_manager._run_git_command(['git', 'remote', 'get-url', 'origin'], local_path)
            
            if remote_check['success']:
                current_url = remote_check['stdout']
                # Limpiar URL si tiene credenciales embebidas
                clean_url = git_manager._clean_url(current_url)
                
                # Si la URL está corrupta o es diferente, actualizarla
                if clean_url != current_url or clean_url != repo_url:
                    logger.info(f"Actualizando remote de {current_url} a {repo_url}")
                    git_manager._run_git_command(['git', 'remote', 'set-url', 'origin', repo_url], local_path)
                    clone_result = {'success': True, 'message': 'Remote actualizado correctamente'}
                else:
                    clone_result = {'success': True, 'message': 'Repositorio ya configurado correctamente'}
            else:
                # No existe remote origin, agregarlo
                logger.info(f"Agregando remote origin: {repo_url}")
                git_manager._run_git_command(['git', 'remote', 'add', 'origin', repo_url], local_path)
                clone_result = {'success': True, 'message': 'Remote agregado correctamente'}
            
            clone_attempted = True
            
        elif data['instance_name'].startswith('prod-'):
            # No existe .git, clonar el repositorio automáticamente para producción
            logger.info(f"Clonando repositorio automáticamente para {data['instance_name']}")
            clone_attempted = True
            
            # Intentar clonar el repositorio
            clone_result = git_manager.clone_repo(
                repo_url=repo_url,
                local_path=local_path,
                branch=data.get('repo_branch', 'main'),
                token=data['github_token']
            )
            
            if clone_result['success']:
                logger.info(f"Repositorio clonado exitosamente para {data['instance_name']}")
            else:
                logger.warning(f"No se pudo clonar el repositorio: {clone_result.get('error')}")
        
        log_action(
            user_id,
            action,
            data['instance_name'],
            f"Repo: {data['repo_owner']}/{data['repo_name']}" + (f" - {clone_result.get('message', 'OK')}" if clone_attempted else ""),
            'success'
        )
        
        response_data = {
            'success': True,
            'message': 'Configuración guardada exitosamente',
            'config': config.to_dict()
        }
        
        if clone_attempted:
            response_data['clone_attempted'] = True
            response_data['clone_success'] = clone_result['success']
            if not clone_result['success']:
                response_data['clone_error'] = clone_result.get('error')
        
        return jsonify(response_data), 200
    except Exception as e:
        db.session.rollback()
        log_action(user_id, 'create_github_config', data.get('instance_name'), str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config/<instance_name>', methods=['DELETE'])
@jwt_required()
def delete_config(instance_name):
    """Elimina (desactiva) una configuración de GitHub"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        config.is_active = False
        db.session.commit()
        
        log_action(user_id, 'delete_github_config', instance_name, 'Configuración desactivada', 'success')
        
        return jsonify({
            'success': True,
            'message': 'Configuración eliminada exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config/<instance_name>/reset', methods=['POST'])
@jwt_required()
def reset_config(instance_name):
    """Resetea completamente la configuración de GitHub para permitir revinculación
    
    Este endpoint:
    1. Limpia el token de acceso existente
    2. Marca la configuración como inactiva
    3. Permite al usuario generar un nuevo token y reconfigurar
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name
        ).first()
        
        if not config:
            return jsonify({
                'success': True,
                'message': 'No existe configuración para resetear',
                'action': 'create_new'
            }), 200
        
        # Limpiar completamente la configuración
        config.github_access_token = None
        config.github_username = None
        config.is_active = False
        config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_action(
            user_id, 
            'reset_github_config', 
            instance_name, 
            'Configuración reseteada - token limpiado', 
            'success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuración reseteada exitosamente. Puedes generar un nuevo token y reconfigurar.',
            'action': 'reconfigure',
            'config': {
                'instance_name': instance_name,
                'repo_owner': config.repo_owner,
                'repo_name': config.repo_name,
                'repo_branch': config.repo_branch,
                'local_path': config.local_path
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        log_action(user_id, 'reset_github_config', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/config/<instance_name>/reconfigure', methods=['POST'])
@jwt_required()
def reconfigure_config(instance_name):
    """Reconfigura una integración existente con un nuevo token
    
    Permite actualizar el token de GitHub sin perder la configuración del repositorio.
    Útil cuando el token expira o se revoca.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('github_token'):
        return jsonify({'error': 'github_token requerido'}), 400
    
    try:
        # Verificar que el token sea válido
        verify_result = git_manager.verify_github_token(data['github_token'])
        if not verify_result['success']:
            return jsonify({
                'success': False,
                'error': 'Token de GitHub inválido',
                'details': verify_result.get('error')
            }), 400
        
        # Buscar configuración existente
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name
        ).first()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'No existe configuración para esta instancia. Usa el endpoint /config para crear una nueva.'
            }), 404
        
        # Actualizar solo el token y reactivar
        config.github_access_token = data['github_token']
        config.github_username = verify_result['username']
        config.is_active = True
        config.updated_at = datetime.utcnow()
        
        # Opcionalmente actualizar otros campos si se proporcionan
        if data.get('repo_owner'):
            config.repo_owner = data['repo_owner']
        if data.get('repo_name'):
            config.repo_name = data['repo_name']
        if data.get('repo_branch'):
            config.repo_branch = data['repo_branch']
        if data.get('local_path'):
            if os.path.exists(data['local_path']):
                config.local_path = data['local_path']
            else:
                return jsonify({'error': f"La ruta {data['local_path']} no existe"}), 400
        
        db.session.commit()
        
        log_action(
            user_id,
            'reconfigure_github_config',
            instance_name,
            f"Token actualizado - Usuario: {verify_result['username']}",
            'success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada exitosamente',
            'config': config.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        log_action(user_id, 'reconfigure_github_config', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/init-repo', methods=['POST'])
@jwt_required()
def init_repo():
    """Inicializa o verifica un repositorio Git en la carpeta local"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('instance_name'):
        return jsonify({'error': 'instance_name requerido'}), 400
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=data['instance_name'],
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Construir URL del repo
        repo_url = f"https://github.com/{config.repo_owner}/{config.repo_name}.git"
        git_dir = os.path.join(config.local_path, '.git')
        
        # Si ya existe el repositorio, verificar y limpiar el remote
        if os.path.exists(git_dir):
            logger.info(f"Repositorio Git ya existe en {config.local_path}, verificando configuración...")
            
            # Obtener URL actual del remote
            remote_check = git_manager._run_git_command(['git', 'remote', 'get-url', 'origin'], config.local_path)
            
            if remote_check['success']:
                current_url = remote_check['stdout']
                # Limpiar URL si tiene credenciales embebidas
                clean_url = git_manager._clean_url(current_url)
                
                # Si la URL está corrupta o es diferente, actualizarla
                if clean_url != current_url or clean_url != repo_url:
                    logger.info(f"Actualizando remote de {current_url} a {repo_url}")
                    update_result = git_manager._run_git_command(['git', 'remote', 'set-url', 'origin', repo_url], config.local_path)
                    
                    if update_result['success']:
                        result = {
                            'success': True,
                            'message': f'Repositorio ya existe. Remote actualizado correctamente a {repo_url}'
                        }
                    else:
                        result = {
                            'success': False,
                            'error': f'No se pudo actualizar el remote: {update_result.get("stderr")}'
                        }
                else:
                    result = {
                        'success': True,
                        'message': 'Repositorio ya existe y está configurado correctamente'
                    }
            else:
                # No existe remote origin, agregarlo
                logger.info(f"Agregando remote origin: {repo_url}")
                add_result = git_manager._run_git_command(['git', 'remote', 'add', 'origin', repo_url], config.local_path)
                
                if add_result['success']:
                    result = {
                        'success': True,
                        'message': f'Remote origin agregado: {repo_url}'
                    }
                else:
                    result = {
                        'success': False,
                        'error': f'No se pudo agregar el remote: {add_result.get("stderr")}'
                    }
        else:
            # No existe .git, inicializar normalmente
            result = git_manager.init_git_repo(
                config.local_path,
                repo_url,
                config.repo_branch,
                config.github_access_token
            )
        
        if result['success']:
            log_action(user_id, 'init_git_repo', data['instance_name'], result['message'], 'success')
            return jsonify(result), 200
        else:
            log_action(user_id, 'init_git_repo', data['instance_name'], result.get('error'), 'error')
            return jsonify(result), 400
    except Exception as e:
        log_action(user_id, 'init_git_repo', data.get('instance_name'), str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/status/<instance_name>', methods=['GET'])
@jwt_required()
def get_status(instance_name):
    """Obtiene el estado del repositorio Git"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        result = git_manager.get_repo_status(config.local_path)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/commit', methods=['POST'])
@jwt_required()
def commit():
    """Crea un commit con los cambios actuales"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('instance_name') or not data.get('message'):
        return jsonify({'error': 'instance_name y message requeridos'}), 400
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=data['instance_name'],
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Usar el nombre y email del usuario de GitHub
        result = git_manager.commit_changes(
            config.local_path,
            data['message'],
            author_name=data.get('author_name', config.github_username),
            author_email=data.get('author_email')
        )
        
        if result['success']:
            log_action(user_id, 'git_commit', data['instance_name'], data['message'], 'success')
            return jsonify(result), 200
        else:
            log_action(user_id, 'git_commit', data['instance_name'], result.get('error'), 'error')
            return jsonify(result), 400
    except Exception as e:
        log_action(user_id, 'git_commit', data.get('instance_name'), str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/push', methods=['POST'])
@jwt_required()
def push():
    """Hace push de los commits al repositorio remoto"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('instance_name'):
        return jsonify({'error': 'instance_name requerido'}), 400
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=data['instance_name'],
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        result = git_manager.push_changes(
            config.local_path,
            config.repo_branch,
            config.github_access_token
        )
        
        if result['success']:
            log_action(user_id, 'git_push', data['instance_name'], 'Push exitoso', 'success')
            return jsonify(result), 200
        else:
            log_action(user_id, 'git_push', data['instance_name'], result.get('error'), 'error')
            return jsonify(result), 400
    except Exception as e:
        log_action(user_id, 'git_push', data.get('instance_name'), str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/pull', methods=['POST'])
@jwt_required()
def pull():
    """Hace pull de los cambios del repositorio remoto"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('instance_name'):
        return jsonify({'error': 'instance_name requerido'}), 400
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=data['instance_name'],
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Verificar si el repositorio está inicializado
        git_dir = os.path.join(config.local_path, '.git')
        if not os.path.exists(git_dir):
            logger.info(f"Repositorio no inicializado en {config.local_path}, inicializando...")
            
            # Construir URL del repo
            repo_url = f"https://github.com/{config.repo_owner}/{config.repo_name}.git"
            
            # Inicializar repo con token
            init_result = git_manager.init_git_repo(
                config.local_path,
                repo_url,
                config.repo_branch,
                config.github_access_token
            )
            
            if not init_result['success']:
                log_action(user_id, 'git_pull', data['instance_name'], f"Error al inicializar: {init_result.get('error')}", 'error')
                return jsonify({
                    'success': False,
                    'error': f"No se pudo inicializar el repositorio: {init_result.get('error')}"
                }), 400
            
            logger.info(f"Repositorio inicializado exitosamente en {config.local_path}")
        
        result = git_manager.pull_changes(
            config.local_path,
            config.repo_branch,
            config.github_access_token
        )
        
        if result['success']:
            log_action(user_id, 'git_pull', data['instance_name'], 'Pull exitoso', 'success')
            return jsonify(result), 200
        else:
            log_action(user_id, 'git_pull', data['instance_name'], result.get('error'), 'error')
            return jsonify(result), 400
    except Exception as e:
        log_action(user_id, 'git_pull', data.get('instance_name'), str(e), 'error')
        return jsonify({'error': str(e)}), 500

@github_bp.route('/history/<instance_name>', methods=['GET'])
@jwt_required()
def get_history(instance_name):
    """Obtiene el historial de commits"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    limit = request.args.get('limit', default=20, type=int)
    limit = min(limit, 100)  # Máximo 100 commits
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        result = git_manager.get_commit_history(config.local_path, limit)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@github_bp.route('/diff/<instance_name>', methods=['GET'])
@jwt_required()
def get_diff(instance_name):
    """Obtiene el diff de archivos modificados"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    file_path = request.args.get('file')
    
    try:
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        result = git_manager.get_file_diff(config.local_path, file_path)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========================================
# WEBHOOK Y AUTO-DEPLOY
# ========================================

@github_bp.route('/webhook/config/<instance_name>', methods=['POST'])
@jwt_required()
def configure_webhook(instance_name):
    """Configura el webhook para auto-deploy"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin']:
        return jsonify({'error': 'Solo administradores pueden configurar webhooks'}), 403
    
    data = request.get_json()
    
    try:
        config = GitHubConfig.query.filter_by(
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Generar secret si no existe
        if not config.webhook_secret:
            config.webhook_secret = secrets.token_hex(32)
        
        # Actualizar configuración
        config.auto_deploy = data.get('auto_deploy', False)
        config.update_modules_on_deploy = data.get('update_modules', False)
        
        # Detectar tipo de instancia
        if instance_name.startswith('dev-'):
            config.instance_type = 'development'
        else:
            config.instance_type = 'production'
            # Asegurar que producción use main
            config.repo_branch = 'main'
        
        db.session.commit()
        
        # Construir URL del webhook
        from flask import current_app
        base_url = current_app.config.get('API_BASE_URL')
        webhook_url = f"{base_url}/api/github/webhook/{instance_name}"
        
        log_action(
            user_id,
            'configure_webhook',
            instance_name,
            f"Auto-deploy: {config.auto_deploy}, Update modules: {config.update_modules_on_deploy}",
            'success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Webhook configurado exitosamente',
            'webhook_url': webhook_url,
            'webhook_secret': config.webhook_secret,
            'config': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_action(user_id, 'configure_webhook', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500


@github_bp.route('/webhook/<instance_name>', methods=['POST'])
def webhook_receiver(instance_name):
    """Recibe webhooks de GitHub y ejecuta auto-deploy"""
    try:
        # Obtener configuración
        config = GitHubConfig.query.filter_by(
            instance_name=instance_name,
            is_active=True,
            auto_deploy=True
        ).first()
        
        if not config:
            return jsonify({
                'error': 'Configuración no encontrada o auto-deploy deshabilitado'
            }), 404
        
        # Verificar signature de GitHub
        signature = request.headers.get('X-Hub-Signature-256')
        if not signature:
            return jsonify({'error': 'Signature no proporcionada'}), 401
        
        # Validar signature
        payload = request.get_data()
        expected_signature = 'sha256=' + hmac.new(
            config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Signature inválida'}), 401
        
        # Parsear payload según Content-Type
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = request.get_json()
        elif 'application/x-www-form-urlencoded' in content_type:
            import json
            payload_str = request.form.get('payload', '{}')
            data = json.loads(payload_str)
        else:
            return jsonify({'error': 'Content-Type no soportado'}), 415
        
        # Verificar que es un push event
        event_type = request.headers.get('X-GitHub-Event')
        
        # Responder OK a ping events
        if event_type == 'ping':
            return jsonify({'message': 'Pong! Webhook configurado correctamente'}), 200
        
        if event_type != 'push':
            return jsonify({
                'message': 'Evento ignorado (solo se procesan push events)'
            }), 200
        
        # Verificar que es la rama correcta
        ref = data.get('ref', '')
        branch = ref.replace('refs/heads/', '')
        
        if branch != config.repo_branch:
            return jsonify({
                'message': f'Rama ignorada (esperada: {config.repo_branch}, recibida: {branch})'
            }), 200
        
        # Extraer información del commit
        commits = data.get('commits', [])
        commit_info = {
            'branch': branch,
            'commits_count': len(commits),
            'pusher': data.get('pusher', {}).get('name'),
            'repository': data.get('repository', {}).get('full_name')
        }
        
        if commits:
            last_commit = commits[-1]
            commit_info['last_commit'] = {
                'id': last_commit.get('id'),
                'message': last_commit.get('message'),
                'author': last_commit.get('author', {}).get('name'),
                'timestamp': last_commit.get('timestamp')
            }
        
        # Ejecutar auto-deploy
        deploy_result = deploy_manager.auto_deploy(config, commit_info)
        
        # Actualizar timestamp de último deploy
        if deploy_result['success']:
            config.last_deploy_at = datetime.utcnow()
            db.session.commit()
        
        # Log de la acción
        log_action(
            config.user_id,
            'webhook_autodeploy',
            instance_name,
            f"Deploy {'exitoso' if deploy_result['success'] else 'fallido'}: {commit_info.get('last_commit', {}).get('message', 'N/A')}",
            'success' if deploy_result['success'] else 'error'
        )
        
        return jsonify({
            'success': deploy_result['success'],
            'message': deploy_result.get('message', 'Deploy procesado'),
            'commit_info': commit_info,
            'deploy_result': deploy_result
        }), 200 if deploy_result['success'] else 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/webhook/test/<instance_name>', methods=['POST'])
@jwt_required()
def test_webhook(instance_name):
    """Prueba el webhook manualmente"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Simular commit info
        commit_info = {
            'branch': config.repo_branch,
            'commits_count': 1,
            'pusher': user.username,
            'repository': f"{config.repo_owner}/{config.repo_name}",
            'test': True
        }
        
        # Ejecutar deploy
        deploy_result = deploy_manager.auto_deploy(config, commit_info)
        
        # Actualizar timestamp si fue exitoso
        if deploy_result['success']:
            config.last_deploy_at = datetime.utcnow()
            db.session.commit()
        
        log_action(
            user_id,
            'test_webhook',
            instance_name,
            f"Test deploy {'exitoso' if deploy_result['success'] else 'fallido'}",
            'success' if deploy_result['success'] else 'error'
        )
        
        return jsonify({
            'success': deploy_result['success'],
            'message': 'Test completado',
            'deploy_result': deploy_result
        }), 200
        
    except Exception as e:
        log_action(user_id, 'test_webhook', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500


@github_bp.route('/current-commit/<instance_name>', methods=['GET'])
@jwt_required()
def get_current_commit(instance_name):
    """Obtiene información del commit actual"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer', 'viewer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = GitHubConfig.query.filter_by(
            instance_name=instance_name,
            is_active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'Configuración no encontrada'}), 404
        
        # Obtener información del commit actual
        result = git_manager.get_commit_history(config.local_path, limit=1)
        
        if result['success'] and result['commits']:
            current_commit = result['commits'][0]
            return jsonify({
                'success': True,
                'commit': {
                    'hash': current_commit['hash'],
                    'short_hash': current_commit['hash'][:7],
                    'message': current_commit['message'],
                    'author': current_commit['author'],
                    'date': current_commit['timestamp'],
                    'email': current_commit.get('email', ''),
                    'branch': config.repo_branch
                },
                'last_deploy': config.last_deploy_at.isoformat() if config.last_deploy_at else None
            }), 200
        else:
            return jsonify({'error': 'No se pudo obtener información del commit'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/branches/<instance_name>', methods=['GET'])
@jwt_required()
def get_branches(instance_name):
    """Obtiene las ramas disponibles del repositorio remoto"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        # Obtener configuración de GitHub
        config = GitHubConfig.query.filter_by(
            user_id=user_id,
            instance_name=instance_name,
            active=True
        ).first()
        
        if not config:
            return jsonify({'error': 'No hay configuración de GitHub para esta instancia'}), 404
        
        # Obtener ramas del repositorio remoto usando git ls-remote
        result = git_manager.get_remote_branches(instance_name)
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Error al obtener ramas')}), 500
        
        return jsonify({
            'success': True,
            'branches': result.get('branches', [])
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@github_bp.route('/deploy-logs/<instance_name>', methods=['GET'])
@jwt_required()
def get_deploy_logs(instance_name):
    """Obtiene los logs de deploy/webhook de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role not in ['admin', 'developer', 'viewer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Obtener logs relacionados con Git/Deploy
        logs = ActionLog.query.filter(
            ActionLog.instance_name == instance_name,
            ActionLog.action.in_([
                'webhook_autodeploy',
                'test_webhook',
                'git_pull',
                'git_push',
                'git_commit'
            ])
        ).order_by(ActionLog.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'logs': [{
                'id': log.id,
                'action': log.action,
                'details': log.details,
                'status': log.status,
                'timestamp': log.timestamp.isoformat(),
                'user': log.user.username if log.user else 'System'
            } for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
