from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ActionLog, db
from services.backup_manager_v2 import BackupManagerV2
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

backup_v2_bp = Blueprint('backup_v2', __name__)
manager = BackupManagerV2()

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
        logger.error(f"Error logging action: {e}")

# ============================================================================
# ENDPOINTS DE GESTIÓN DE INSTANCIAS
# ============================================================================

@backup_v2_bp.route('/instances', methods=['GET'])
@jwt_required()
def list_instances():
    """Lista todas las instancias con configuración de backup"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.list_instances_with_backups()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing instances: {e}")
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/backups/<filename>/rename', methods=['POST'])
@jwt_required()
def rename_instance_backup(instance_name, filename):
    """Renombra un backup específico"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    try:
        data = request.get_json() or {}
        new_filename = data.get('new_filename')
        if not new_filename:
            return jsonify({'error': 'Se requiere new_filename'}), 400

        result = manager.rename_backup(instance_name, filename, new_filename)

        log_action(
            user_id,
            'rename_backup',
            instance_name,
            f"{filename} -> {new_filename}",
            'success' if result.get('success') else 'error'
        )

        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Error renaming backup {filename} for {instance_name}: {e}")
        log_action(user_id, 'rename_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/config', methods=['GET'])
@jwt_required()
def get_instance_config(instance_name):
    """Obtiene la configuración de backup de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_instance_config(instance_name)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting config for {instance_name}: {e}")
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/config', methods=['PUT'])
@jwt_required()
def update_instance_config(instance_name):
    """Actualiza la configuración de backup de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json() or {}
        
        result = manager.update_instance_config(
            instance_name,
            auto_backup_enabled=data.get('auto_backup_enabled'),
            schedule=data.get('schedule'),
            retention_days=data.get('retention_days'),
            priority=data.get('priority')
        )
        
        log_action(
            user_id,
            'update_backup_config',
            instance_name,
            f"Config updated: {data}",
            'success' if result['success'] else 'error'
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error updating config for {instance_name}: {e}")
        log_action(user_id, 'update_backup_config', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/toggle', methods=['POST'])
@jwt_required()
def toggle_auto_backup(instance_name):
    """Activa o pausa el backup automático de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json() or {}
        enabled = data.get('enabled', True)
        
        result = manager.toggle_auto_backup(instance_name, enabled)
        
        action_msg = 'enabled' if enabled else 'disabled'
        log_action(
            user_id,
            'toggle_auto_backup',
            instance_name,
            f"Auto backup {action_msg}",
            'success' if result['success'] else 'error'
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error toggling backup for {instance_name}: {e}")
        log_action(user_id, 'toggle_auto_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINTS DE BACKUPS
# ============================================================================

@backup_v2_bp.route('/instances/<instance_name>/backups', methods=['GET'])
@jwt_required()
def list_instance_backups(instance_name):
    """Lista todos los backups de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.list_backups(instance_name)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error listing backups for {instance_name}: {e}")
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/backup', methods=['POST'])
@jwt_required()
def create_instance_backup(instance_name):
    """Crea un backup manual de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json(silent=True) or {}
        custom_filename = data.get('custom_filename')

        result = manager.create_backup(instance_name, custom_filename=custom_filename)
        
        log_action(
            user_id,
            'create_backup',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error creating backup for {instance_name}: {e}")
        log_action(user_id, 'create_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/backups/<filename>', methods=['DELETE'])
@jwt_required()
def delete_instance_backup(instance_name, filename):
    """Elimina un backup específico de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.delete_backup(instance_name, filename)
        
        log_action(
            user_id,
            'delete_backup',
            instance_name,
            f"Deleted: {filename}",
            'success' if result['success'] else 'error'
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting backup {filename} for {instance_name}: {e}")
        log_action(user_id, 'delete_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/backups/<filename>/download', methods=['GET'])
@jwt_required()
def download_instance_backup(instance_name, filename):
    """Descarga un backup específico"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        instance_dir = manager._get_instance_dir(instance_name)
        backup_path = os.path.join(instance_dir, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup no encontrado'}), 404
        
        if not manager._is_safe_backup_filename(filename):
            return jsonify({'error': 'Nombre de archivo inválido'}), 400
        
        log_action(user_id, 'download_backup', instance_name, f"Downloaded: {filename}", 'success')
        
        mimetype = 'application/zip' if filename.endswith('.zip') else 'application/gzip'

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    except Exception as e:
        logger.error(f"Error downloading backup {filename} for {instance_name}: {e}")
        log_action(user_id, 'download_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/restore', methods=['POST'])
@jwt_required()
def restore_instance_backup(instance_name):
    """Restaura un backup de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json() or {}
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Se requiere el nombre del archivo'}), 400
        
        result = manager.restore_backup(instance_name, filename)
        
        log_action(
            user_id,
            'restore_backup',
            instance_name,
            f"Restoring: {filename}",
            'success' if result['success'] else 'error'
        )
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error restoring backup for {instance_name}: {e}")
        log_action(user_id, 'restore_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINTS DE LOGS
# ============================================================================

@backup_v2_bp.route('/instances/<instance_name>/backup-log', methods=['GET'])
@jwt_required()
def get_instance_backup_log(instance_name):
    """Obtiene el log del último backup de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_backup_log(instance_name)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting backup log for {instance_name}: {e}")
        return jsonify({'error': str(e)}), 500

@backup_v2_bp.route('/instances/<instance_name>/restore-log', methods=['GET'])
@jwt_required()
def get_instance_restore_log(instance_name):
    """Obtiene el log de la última restauración de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_restore_log(instance_name)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting restore log for {instance_name}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINTS DE ESTADÍSTICAS
# ============================================================================

@backup_v2_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_global_stats():
    """Obtiene estadísticas globales de todos los backups"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_global_stats()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting global stats: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT DE UPLOAD
# ============================================================================

@backup_v2_bp.route('/instances/<instance_name>/upload', methods=['POST'])
@jwt_required()
def upload_backup(instance_name):
    """Sube un archivo de backup para una instancia específica"""
    import sys
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    logger.info("=" * 80)
    logger.info(f"🎯 ENDPOINT /instances/{instance_name}/upload LLAMADO")
    logger.info(f"📋 Request method: {request.method}")
    logger.info(f"📋 Request content_type: {request.content_type}")
    sys.stdout.flush()
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        logger.info(f"📥 Request de upload recibido de usuario {user_id} ({user.username})")
        
        if 'file' not in request.files:
            logger.error("❌ No se encontró el archivo en la petición")
            return jsonify({'error': 'No se proporcionó ningún archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.error("❌ Nombre de archivo vacío")
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        
        # Validar extensión
        if not (file.filename.endswith('.tar.gz') or file.filename.endswith('.zip')):
            logger.error(f"❌ Extensión inválida: {file.filename}")
            return jsonify({'error': 'El archivo debe ser .tar.gz o .zip'}), 400
        
        logger.info("🚀 Iniciando proceso de upload...")
        sys.stdout.flush()
        
        result = manager.upload_backup(instance_name, file)
        
        logger.info(f"📊 Resultado del upload: {result}")
        logger.info("=" * 80)
        sys.stdout.flush()
        
        if result['success']:
            log_action(
                user_id,
                'upload_backup',
                instance_name,
                f"Backup: {result['filename']}",
                'success'
            )
        else:
            log_action(user_id, 'upload_backup', instance_name, result.get('error'), 'error')
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"💥 EXCEPCIÓN EN UPLOAD: {str(e)}")
        logger.exception("Stack trace:")
        sys.stdout.flush()
        log_action(user_id, 'upload_backup', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500
