from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.instance_manager import InstanceManager
from models import db, ActionLog, User

instances_bp = Blueprint('instances', __name__)
manager = InstanceManager()

def log_action(user_id, action, instance_name=None, details=None, status='success'):
    """Registra una acción en el log"""
    try:
        log = ActionLog(
            user_id=user_id,
            action=action,
            instance_name=instance_name,
            details=details,
            status=status
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
        db.session.rollback()

@instances_bp.route('', methods=['GET'])
@jwt_required()
def list_instances():
    """Lista todas las instancias"""
    try:
        instances = manager.list_instances()
        return jsonify({'instances': instances, 'count': len(instances)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>', methods=['GET'])
@jwt_required()
def get_instance(instance_name):
    """Obtiene información detallada de una instancia"""
    try:
        instance = manager.get_instance_status(instance_name)
        if not instance:
            return jsonify({'error': 'Instancia no encontrada'}), 404
        return jsonify(instance), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/create', methods=['POST'])
@jwt_required()
def create_instance():
    """Crea una nueva instancia de desarrollo"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre de instancia requerido'}), 400
    
    try:
        result = manager.create_dev_instance(data['name'])
        
        # Log
        log_action(
            user_id,
            'create_instance',
            f"dev-{data['name']}",
            f"Creación iniciada: {result.get('message')}",
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 202  # Accepted
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'create_instance', f"dev-{data['name']}", str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>', methods=['DELETE'])
@jwt_required()
def delete_instance(instance_name):
    """Elimina una instancia de desarrollo"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role != 'admin':
        return jsonify({'error': 'Solo administradores pueden eliminar instancias'}), 403
    
    try:
        result = manager.delete_instance(instance_name)
        
        # Log
        log_action(
            user_id,
            'delete_instance',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'delete_instance', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>/update-db', methods=['POST'])
@jwt_required()
def update_instance_db(instance_name):
    """Actualiza la base de datos de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.update_instance_db(instance_name)
        
        # Log
        log_action(
            user_id,
            'update_db',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'update_db', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>/update-files', methods=['POST'])
@jwt_required()
def update_instance_files(instance_name):
    """Actualiza los archivos de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.update_instance_files(instance_name)
        
        # Log
        log_action(
            user_id,
            'update_files',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'update_files', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>/logs', methods=['GET'])
@jwt_required()
def get_instance_logs(instance_name):
    """Obtiene los logs de una instancia"""
    lines = request.args.get('lines', default=100, type=int)
    lines = min(lines, 1000)  # Máximo 1000 líneas
    log_type = request.args.get('type', default='systemd', type=str)
    
    try:
        result = manager.get_instance_logs(instance_name, lines, log_type)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>/restart', methods=['POST'])
@jwt_required()
def restart_instance(instance_name):
    """Reinicia una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.restart_instance(instance_name)
        
        # Log
        log_action(
            user_id,
            'restart_instance',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'restart_instance', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/creation-log/<instance_name>', methods=['GET'])
@jwt_required()
def get_creation_log(instance_name):
    """Obtiene el log de creación de una instancia"""
    import os
    
    log_file = f'/tmp/odoo-create-dev-{instance_name}.log'
    
    if not os.path.exists(log_file):
        return jsonify({'log': 'Log no disponible aún...', 'exists': False}), 200
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        return jsonify({'log': content, 'exists': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/update-log/<instance_name>/<action>', methods=['GET'])
@jwt_required()
def get_update_log(instance_name, action):
    """Obtiene el log de actualización de una instancia"""
    import os
    
    log_files = {
        'update-db': f'/tmp/odoo-update-db-{instance_name}.log',
        'update-files': f'/tmp/odoo-update-files-{instance_name}.log',
        'sync-filestore': f'/tmp/odoo-sync-filestore-{instance_name}.log'
    }
    
    log_file = log_files.get(action)
    if not log_file:
        return jsonify({'error': 'Acción no válida'}), 400
    
    if not os.path.exists(log_file):
        return jsonify({'log': 'Log no disponible aún...', 'exists': False}), 200
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        return jsonify({'log': content, 'exists': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/<instance_name>/sync-filestore', methods=['POST'])
@jwt_required()
def sync_instance_filestore(instance_name):
    """Sincroniza el filestore de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.sync_filestore(instance_name)
        
        # Log
        log_action(
            user_id,
            'sync_filestore',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'sync_filestore', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500
