from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ActionLog, db
from services.backup_manager import BackupManager
import os
from datetime import datetime

backup_bp = Blueprint('backup', __name__)
manager = BackupManager()

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

@backup_bp.route('/list', methods=['GET'])
@jwt_required()
def list_backups():
    """Lista todos los backups disponibles"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede ver backups
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.list_backups()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/create', methods=['POST'])
@jwt_required()
def create_backup():
    """Crea un nuevo backup"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede crear backups
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.create_backup()
        
        # Log
        log_action(
            user_id,
            'create_backup',
            'production',
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'create_backup', 'production', str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_backup(filename):
    """Descarga un backup específico"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede descargar backups
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    # Validar nombre de archivo
    if not filename.startswith('backup_') or not filename.endswith('.tar.gz'):
        return jsonify({'error': 'Nombre de archivo inválido'}), 400
    
    backup_path = os.path.join(manager.backup_dir, filename)
    
    if not os.path.exists(backup_path):
        return jsonify({'error': 'Backup no encontrado'}), 404
    
    try:
        # Log
        log_action(user_id, 'download_backup', filename, 'Descarga iniciada', 'success')
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/gzip'
        )
    except Exception as e:
        log_action(user_id, 'download_backup', filename, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/delete/<filename>', methods=['DELETE'])
@jwt_required()
def delete_backup(filename):
    """Elimina un backup específico"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede eliminar backups
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.delete_backup(filename)
        
        # Log
        log_action(
            user_id,
            'delete_backup',
            filename,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'delete_backup', filename, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """Obtiene la configuración de backups"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede ver configuración
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        config = manager.get_config()
        return jsonify(config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/config', methods=['PUT'])
@jwt_required()
def update_config():
    """Actualiza la configuración de backups"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede actualizar configuración
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json()
        result = manager.update_config(
            retention_days=data.get('retention_days'),
            schedule=data.get('schedule'),
            auto_backup_enabled=data.get('auto_backup_enabled')
        )
        
        # Log
        log_action(
            user_id,
            'update_backup_config',
            'configuration',
            f"Retención: {data.get('retention_days')} días",
            'success'
        )
        
        return jsonify(result), 200
    except Exception as e:
        log_action(user_id, 'update_backup_config', 'configuration', str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/log', methods=['GET'])
@jwt_required()
def get_backup_log():
    """Obtiene el log del último backup"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede ver logs
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_backup_log()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
