from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, GitHubConfig, ActionLog
from services.git_manager import GitManager
from datetime import datetime
import os

github_bp = Blueprint('github', __name__)
git_manager = GitManager()

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
        
        log_action(
            user_id,
            action,
            data['instance_name'],
            f"Repo: {data['repo_owner']}/{data['repo_name']}",
            'success'
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuración guardada exitosamente',
            'config': config.to_dict()
        }), 200
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
    """Inicializa un repositorio Git en la carpeta local"""
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
        
        # Inicializar repo
        result = git_manager.init_git_repo(
            config.local_path,
            repo_url,
            config.repo_branch
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
