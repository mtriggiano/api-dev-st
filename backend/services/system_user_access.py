import logging
import os
import pwd
import re
import subprocess

from flask import current_app

logger = logging.getLogger(__name__)

_INSTANCE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9._-]+$')


def get_system_username(user):
    if not user or not getattr(user, 'id', None):
        raise ValueError('Usuario inválido para sincronizar usuario de servidor')
    return f'apidev_u{user.id}'


def get_system_user_status(user):
    system_username = get_system_username(user)
    try:
        pwd.getpwnam(system_username)
        exists = True
    except KeyError:
        exists = False

    return {
        'system_username': system_username,
        'system_user_exists': exists,
    }


def _normalize_instance_names(instance_names):
    normalized = set()

    for name in instance_names or []:
        if not isinstance(name, str):
            continue

        candidate = name.strip()
        if candidate and _INSTANCE_NAME_PATTERN.match(candidate):
            normalized.add(candidate)

    return sorted(normalized)


def sync_system_user_instance_access(user, instance_names=None):
    """
    Sincroniza el usuario Linux ligado al usuario API-DEV y aplica ACL por instancia.
    - No altera ownership del core de carpetas
    - Usa ACL para dar/quitar permisos por instancia
    """
    system_username = get_system_username(user)

    if user.role == 'admin':
        return {
            'success': True,
            'system_username': system_username,
            'skipped': True,
            'reason': 'Rol admin no requiere ACL por instancia',
        }

    if instance_names is None:
        instance_names = user.assigned_instances()

    normalized_instances = _normalize_instance_names(instance_names)

    scripts_path = current_app.config['SCRIPTS_PATH']
    script_path = current_app.config.get(
        'SYSTEM_USER_SYNC_SCRIPT',
        os.path.join(scripts_path, 'users', 'sync-instance-access.sh')
    )

    if not os.path.exists(script_path):
        raise FileNotFoundError(f'Script de sincronización no encontrado: {script_path}')

    command = [
        '/bin/bash',
        script_path,
        system_username,
        current_app.config['PROD_ROOT'],
        current_app.config['DEV_ROOT'],
        *normalized_instances,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=240,
    )

    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()

    if result.returncode != 0:
        details = stderr or stdout or 'Sin detalle'
        logger.error('Error sincronizando ACL para %s: %s', system_username, details)
        raise RuntimeError(f'Error sincronizando permisos del servidor: {details}')

    return {
        'success': True,
        'system_username': system_username,
        'assigned_instances': normalized_instances,
        'output': stdout,
    }


def set_system_user_ssh_public_key(user, public_key):
    """
    Provisiona la clave pública SSH para el usuario Linux ligado al usuario API-DEV.
    Reemplaza authorized_keys por la clave provista para mantener operación simple.
    """
    system_username = get_system_username(user)
    key_value = (public_key or '').strip()

    if not key_value:
        raise ValueError('La clave pública SSH es requerida')

    scripts_path = current_app.config['SCRIPTS_PATH']
    script_path = current_app.config.get(
        'SYSTEM_USER_SSH_KEY_SCRIPT',
        os.path.join(scripts_path, 'users', 'set-ssh-public-key.sh')
    )

    if not os.path.exists(script_path):
        raise FileNotFoundError(f'Script de clave SSH no encontrado: {script_path}')

    result = subprocess.run(
        ['/bin/bash', script_path, system_username],
        input=f'{key_value}\n',
        capture_output=True,
        text=True,
        timeout=120,
    )

    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()

    if result.returncode != 0:
        details = stderr or stdout or 'Sin detalle'
        logger.error('Error configurando SSH key para %s: %s', system_username, details)
        raise RuntimeError(f'Error configurando clave SSH: {details}')

    return {
        'success': True,
        'system_username': system_username,
        'output': stdout,
    }


def revoke_system_user_ssh_public_key(user):
    """Revoca (vacía) authorized_keys del usuario Linux ligado a API-DEV."""
    system_username = get_system_username(user)

    scripts_path = current_app.config['SCRIPTS_PATH']
    script_path = current_app.config.get(
        'SYSTEM_USER_SSH_KEY_SCRIPT',
        os.path.join(scripts_path, 'users', 'set-ssh-public-key.sh')
    )

    if not os.path.exists(script_path):
        raise FileNotFoundError(f'Script de clave SSH no encontrado: {script_path}')

    result = subprocess.run(
        ['/bin/bash', script_path, system_username, '--clear'],
        capture_output=True,
        text=True,
        timeout=120,
    )

    stdout = (result.stdout or '').strip()
    stderr = (result.stderr or '').strip()

    if result.returncode != 0:
        details = stderr or stdout or 'Sin detalle'
        logger.error('Error revocando SSH key para %s: %s', system_username, details)
        raise RuntimeError(f'Error revocando clave SSH: {details}')

    return {
        'success': True,
        'system_username': system_username,
        'output': stdout,
    }
