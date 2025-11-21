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

@instances_bp.route('/production-instances', methods=['GET'])
@jwt_required()
def get_production_instances():
    """Lista las instancias de producción disponibles para clonar"""
    try:
        instances = manager.list_production_instances()
        return jsonify({'instances': instances}), 200
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
    
    # Obtener instancia de producción a clonar (opcional)
    source_instance = data.get('sourceInstance')
    
    # Obtener opción de neutralización (por defecto True)
    neutralize = data.get('neutralize', True)
    
    try:
        result = manager.create_dev_instance(data['name'], source_instance, neutralize)
        
        # Log
        source_msg = f" desde {source_instance}" if source_instance else ""
        neutralize_msg = " (neutralizada)" if neutralize else " (sin neutralizar)"
        log_action(
            user_id,
            'create_instance',
            f"dev-{data['name']}",
            f"Creación iniciada{source_msg}{neutralize_msg}: {result.get('message')}",
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 202  # Accepted
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'create_instance', f"dev-{data['name']}", str(e), 'error')
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/odoo-versions', methods=['GET'])
@jwt_required()
def get_odoo_versions():
    """Obtiene las versiones de Odoo disponibles"""
    try:
        versions = [
            {'version': '19', 'edition': 'enterprise', 'label': 'Odoo 19 Enterprise'},
            {'version': '19', 'edition': 'community', 'label': 'Odoo 19 Community'},
            {'version': '18', 'edition': 'enterprise', 'label': 'Odoo 18 Enterprise'},
            {'version': '18', 'edition': 'community', 'label': 'Odoo 18 Community'}
        ]
        return jsonify({'success': True, 'versions': versions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@instances_bp.route('/create-production', methods=['POST'])
@jwt_required()
def create_production_instance():
    """Crea una nueva instancia de producción con subdominio obligatorio
    
    Body params:
        - name: Nombre de la instancia (será usado como subdominio)
        - version: Versión de Odoo (19 o 18) - opcional, default: 19
        - edition: Edición (enterprise o community) - opcional, default: enterprise
        - ssl_method: Método SSL (cloudflare, letsencrypt, http) - opcional, default: letsencrypt
    
    IMPORTANTE: El nombre será usado como subdominio. 
    Ejemplo: name="cliente1" creará cliente1.softrigx.com
    NUNCA se usará el dominio raíz directamente.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo administradores pueden crear instancias de producción
    if user.role != 'admin':
        return jsonify({'error': 'Solo administradores pueden crear instancias de producción'}), 403
    
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Nombre de instancia requerido'}), 400
    
    name = data['name'].strip().lower()
    version = data.get('version', '19')
    edition = data.get('edition', 'enterprise')
    ssl_method = data.get('ssl_method', 'letsencrypt')
    
    # Validación adicional en el endpoint
    if not name:
        return jsonify({'error': 'El nombre no puede estar vacío'}), 400
    
    # Validar versión y edición
    if version not in ['18', '19']:
        return jsonify({'error': 'Versión debe ser 18 o 19'}), 400
    
    if edition not in ['enterprise', 'community']:
        return jsonify({'error': 'Edición debe ser enterprise o community'}), 400
    
    try:
        result = manager.create_prod_instance(name, version, edition, ssl_method)
        
        # Log
        log_action(
            user_id,
            'create_production_instance',
            result.get('instance_name', f'prod-{name}'),
            f"Creación iniciada: {result.get('message')} - SSL: {ssl_method}",
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 202  # Accepted
        else:
            return jsonify(result), 400 if 'prohibido' in result.get('error', '').lower() or 'inválido' in result.get('error', '').lower() else 500
    except Exception as e:
        log_action(user_id, 'create_production_instance', f'prod-{name}', str(e), 'error')
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

@instances_bp.route('/production/<instance_name>', methods=['DELETE'])
@jwt_required()
def delete_production_instance(instance_name):
    """Elimina una instancia de producción con doble confirmación"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Solo administradores pueden eliminar instancias de producción
    if user.role != 'admin':
        return jsonify({'error': 'Solo administradores pueden eliminar instancias de producción'}), 403
    
    try:
        # Obtener confirmación del request
        data = request.get_json() or {}
        confirmation = data.get('confirmation', '')
        
        if not confirmation:
            return jsonify({'error': 'Se requiere confirmación para eliminar'}), 400
        
        result = manager.delete_production_instance(instance_name, confirmation)
        
        # Log
        log_action(
            user_id,
            'delete_production_instance',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'delete_production_instance', instance_name, str(e), 'error')
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
        # Obtener parámetro de neutralización (por defecto True)
        data = request.get_json() or {}
        neutralize = data.get('neutralize', True)
        
        result = manager.update_instance_db(instance_name, neutralize=neutralize)
        
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
    """Obtiene log incremental + estado + pid de creación"""
    import os

    # Paths
    log_file = f'/tmp/odoo-create-{instance_name}.log'
    pid_file = f'/tmp/{instance_name}.pid'
    status_file = f'/tmp/{instance_name}.status'

    # Si el log aún no existe
    if not os.path.exists(log_file):
        return jsonify({
            'exists': False,
            'log': 'Log no disponible aún...',
            'pid': None,
            'status': 'pending',
            'finished': False,
            'error': False
        }), 200

    # Leer últimas 5000 bytes estilo tail
    try:
        with open(log_file, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            offset = max(size - 5000, 0)
            f.seek(offset)
            log_content = f.read().decode(errors="replace")
    except Exception as e:
        return jsonify({'error': f'Error leyendo log: {e}'}), 500

    # Leer PID
    pid = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
        except:
            pid = None

    # Leer estado
    status = "running"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = f.read().strip()
        except:
            status = "unknown"

    finished = (status == "success")
    error = (status == "error")

    return jsonify({
        'exists': True,
        'log': log_content,
        'pid': pid,
        'status': status,
        'finished': finished,
        'error': error
    }), 200

@instances_bp.route('/update-log/<instance_name>/<action>', methods=['GET'])
@jwt_required()
def get_update_log(instance_name, action):
    """Obtiene el log de actualización de una instancia"""
    import os
    
    log_files = {
        'update-db': f'/tmp/odoo-update-db-{instance_name}.log',
        'update-files': f'/tmp/odoo-update-files-{instance_name}.log',
        'sync-filestore': f'/tmp/odoo-sync-filestore-{instance_name}.log',
        'regenerate-assets': f'/tmp/odoo-regenerate-assets-{instance_name}.log'
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

@instances_bp.route('/<instance_name>/regenerate-assets', methods=['POST'])
@jwt_required()
def regenerate_instance_assets(instance_name):
    """Regenera los assets de una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    # Verificar permisos
    if user.role not in ['admin', 'developer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        result = manager.regenerate_assets(instance_name)
        
        # Log
        log_action(
            user_id,
            'regenerate_assets',
            instance_name,
            result.get('message') or result.get('error'),
            'success' if result['success'] else 'error'
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    except Exception as e:
        log_action(user_id, 'regenerate_assets', instance_name, str(e), 'error')
        return jsonify({'error': str(e)}), 500
