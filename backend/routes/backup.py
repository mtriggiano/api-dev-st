from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, ActionLog, db
from services.backup_manager import BackupManager
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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

@backup_bp.route('/restore', methods=['POST'])
@jwt_required()
def restore_backup():
    """Restaura un backup de producción"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede restaurar
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename requerido'}), 400
        
        # Confirmar que el usuario entiende los riesgos
        confirmed = data.get('confirmed', False)
        if not confirmed:
            return jsonify({'error': 'Debe confirmar la restauración'}), 400
        
        result = manager.restore_backup(filename)
        
        if result['success']:
            log_action(
                user_id,
                'restore_backup',
                'production',
                f"Backup: {filename}",
                'success'
            )
        else:
            log_action(user_id, 'restore_backup', 'production', result.get('error'), 'error')
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        log_action(user_id, 'restore_backup', 'production', str(e), 'error')
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/restore/log', methods=['GET'])
@jwt_required()
def get_restore_log():
    """Obtiene el log de la última restauración"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo admin puede ver logs
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.get_restore_log()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_backup():
    """Sube un archivo de backup"""
    import sys
    logger.info("=" * 80)
    logger.info("🎯 ENDPOINT /upload LLAMADO")
    logger.info(f"📋 Request method: {request.method}")
    logger.info(f"📋 Request headers: {dict(request.headers)}")
    logger.info(f"📋 Request content_type: {request.content_type}")
    logger.info(f"📋 Request content_length: {request.content_length}")
    logger.info(f"📋 Request files keys: {list(request.files.keys())}")
    logger.info(f"📋 Request form keys: {list(request.form.keys())}")
    sys.stdout.flush()
    
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    logger.info(f"📥 Request de upload recibido de usuario {user_id} ({user.username})")
    
    # Solo admin puede subir backups
    if user.role != 'admin':
        logger.warning(f"⚠️ Usuario {user_id} sin permisos de admin intentó subir backup")
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            logger.error("❌ No se envió ningún archivo en el request")
            logger.error(f"❌ Files disponibles: {list(request.files.keys())}")
            return jsonify({'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['file']
        
        logger.info(f"📄 Archivo recibido: {file.filename}")
        logger.info(f"📊 Content-Type: {file.content_type}")
        logger.info(f"📊 File stream: {file.stream}")
        
        if file.filename == '':
            logger.error("❌ Nombre de archivo vacío")
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        # Validar extensión
        if not (file.filename.endswith('.tar.gz') or file.filename.endswith('.zip')):
            logger.error(f"❌ Extensión inválida: {file.filename}")
            return jsonify({'error': 'El archivo debe ser .tar.gz o .zip'}), 400
        
        logger.info("🚀 Iniciando proceso de upload...")
        sys.stdout.flush()
        
        result = manager.upload_backup(file)
        
        logger.info(f"📊 Resultado del upload: {result}")
        logger.info("=" * 80)
        sys.stdout.flush()
        
        if result['success']:
            log_action(
                user_id,
                'upload_backup',
                'production',
                f"Backup: {result['filename']}",
                'success'
            )
        else:
            log_action(user_id, 'upload_backup', 'production', result.get('error'), 'error')
        
        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"💥 EXCEPCIÓN EN UPLOAD: {str(e)}")
        logger.exception("Stack trace:")
        sys.stdout.flush()
        log_action(user_id, 'upload_backup', 'production', str(e), 'error')
        return jsonify({'error': str(e)}), 500
