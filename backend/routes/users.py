from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, UserProfile
from services.instance_manager import InstanceManager
from services.access_control import normalize_instance_names, sync_user_instance_access

users_bp = Blueprint('users', __name__)
manager = InstanceManager()

VALID_ROLES = {'admin', 'developer', 'viewer'}


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _ensure_profile(user):
    if not user.profile:
        user.profile = UserProfile(first_name='', last_name='')
    return user.profile


@users_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """Lista usuarios del sistema (solo admin)"""
    current_user = _get_current_user()
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    users = User.query.order_by(User.username.asc()).all()
    return jsonify({'users': [user.to_dict() for user in users]}), 200


@users_bp.route('/available-instances', methods=['GET'])
@jwt_required()
def list_available_instances():
    """Lista instancias disponibles para asignación (solo admin)"""
    current_user = _get_current_user()
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    instances = manager.list_instances()
    instances = sorted(instances, key=lambda instance: instance.get('name', ''))

    return jsonify({
        'instances': [
            {
                'name': instance.get('name'),
                'type': instance.get('type'),
                'domain': instance.get('domain'),
            }
            for instance in instances
        ]
    }), 200


@users_bp.route('', methods=['POST'])
@jwt_required()
def create_user():
    """Crea un nuevo usuario y asigna instancias (solo admin)"""
    current_user = _get_current_user()
    if not current_user or current_user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json() or {}

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    role = (data.get('role') or 'viewer').strip()

    if not username:
        return jsonify({'error': 'Usuario requerido'}), 400

    if not password:
        return jsonify({'error': 'Contraseña requerida'}), 400

    if role not in VALID_ROLES:
        return jsonify({'error': 'Rol inválido'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'El usuario ya existe'}), 409

    try:
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = _ensure_profile(user)
        profile.first_name = (data.get('first_name') or '').strip()
        profile.last_name = (data.get('last_name') or '').strip()

        sync_user_instance_access(user, normalize_instance_names(data.get('assigned_instances', [])))

        db.session.commit()
        return jsonify({'message': 'Usuario creado exitosamente', 'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Actualiza una cuenta de usuario"""
    current_user = _get_current_user()
    if not current_user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    is_admin = current_user.role == 'admin'
    is_self = current_user.id == user.id

    if not is_admin and not is_self:
        return jsonify({'error': 'Permisos insuficientes'}), 403

    data = request.get_json() or {}

    if not is_admin and any(field in data for field in ('role', 'username', 'assigned_instances')):
        return jsonify({'error': 'Solo administradores pueden actualizar rol, usuario o asignaciones'}), 403

    try:
        if is_admin and 'username' in data:
            new_username = (data.get('username') or '').strip()
            if not new_username:
                return jsonify({'error': 'Usuario requerido'}), 400

            existing = User.query.filter(User.username == new_username, User.id != user.id).first()
            if existing:
                return jsonify({'error': 'El usuario ya existe'}), 409
            user.username = new_username

        if is_admin and 'role' in data:
            new_role = (data.get('role') or '').strip()
            if new_role not in VALID_ROLES:
                return jsonify({'error': 'Rol inválido'}), 400

            if is_self and new_role != 'admin':
                return jsonify({'error': 'No puedes quitarte permisos de administrador'}), 400
            user.role = new_role

        if 'first_name' in data or 'last_name' in data:
            profile = _ensure_profile(user)
            if 'first_name' in data:
                profile.first_name = (data.get('first_name') or '').strip()
            if 'last_name' in data:
                profile.last_name = (data.get('last_name') or '').strip()

        if 'password' in data and data.get('password'):
            user.set_password(data.get('password'))

        if is_admin and 'assigned_instances' in data:
            sync_user_instance_access(user, normalize_instance_names(data.get('assigned_instances') or []))

        db.session.commit()
        return jsonify({'message': 'Usuario actualizado exitosamente', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
