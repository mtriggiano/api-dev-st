from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from config import Config
import os
import re
from collections import deque

odoo_logs_bp = Blueprint('odoo_logs', __name__)

# Regex para parsear líneas de log de Odoo
# Formato: 2026-02-08 15:03:42,089 1200 WARNING dev-mtg-production odoo.http: mensaje
LOG_LINE_REGEX = re.compile(
    r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+'  # timestamp
    r'(\d+)\s+'                                              # pid
    r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+'                # level
    r'(\S+)\s+'                                              # database
    r'(\S+):\s*'                                             # logger
    r'(.*)'                                                  # message
)


def _get_instance_log_path(instance_name):
    """Obtiene la ruta base de logs para una instancia dinámicamente"""
    # Verificar en producción
    prod_path = os.path.join(Config.PROD_ROOT, instance_name)
    if os.path.isdir(prod_path):
        return prod_path
    
    # Verificar en desarrollo
    dev_path = os.path.join(Config.DEV_ROOT, instance_name)
    if os.path.isdir(dev_path):
        return dev_path
    
    return None


def _get_service_name(instance_name):
    """Obtiene el nombre del servicio systemd para una instancia"""
    # Intentar detectar el servicio automáticamente
    import subprocess
    try:
        result = subprocess.run(
            ['systemctl', 'list-units', '--type=service', '--no-pager', '-q'],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.split('\n'):
            if instance_name in line and 'odoo' in line.lower():
                return line.strip().split()[0].replace('.service', '')
    except:
        pass
    
    # Fallback: intentar nombres comunes
    candidates = [
        f'odoo19e-{instance_name}',
        f'odoo-{instance_name}',
        f'odoo19-{instance_name}',
    ]
    for candidate in candidates:
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', candidate],
                capture_output=True, text=True, timeout=3
            )
            if result.stdout.strip() in ('active', 'inactive', 'failed'):
                return candidate
        except:
            continue
    
    return None


def tail_file(filepath, lines=500):
    """Lee las últimas N líneas de un archivo de forma eficiente"""
    try:
        with open(filepath, 'rb') as f:
            # Ir al final del archivo
            f.seek(0, 2)
            file_size = f.tell()
            
            if file_size == 0:
                return []
            
            # Buffer para leer bloques
            block_size = 8192
            blocks = []
            remaining = file_size
            found_lines = 0
            
            while remaining > 0 and found_lines < lines + 1:
                read_size = min(block_size, remaining)
                remaining -= read_size
                f.seek(remaining)
                block = f.read(read_size)
                blocks.insert(0, block)
                found_lines += block.count(b'\n')
            
            content = b''.join(blocks).decode('utf-8', errors='replace')
            all_lines = content.split('\n')
            
            # Devolver las últimas N líneas (sin línea vacía final)
            if all_lines and all_lines[-1] == '':
                all_lines = all_lines[:-1]
            
            return all_lines[-lines:]
    except Exception as e:
        return [f"Error leyendo archivo: {str(e)}"]


def parse_log_line(line):
    """Parsea una línea de log de Odoo y extrae sus componentes"""
    match = LOG_LINE_REGEX.match(line)
    if match:
        return {
            'timestamp': match.group(1),
            'pid': match.group(2),
            'level': match.group(3),
            'database': match.group(4),
            'logger': match.group(5),
            'message': match.group(6),
            'raw': line
        }
    # Línea de continuación (traceback, etc.)
    return {
        'timestamp': '',
        'pid': '',
        'level': 'CONTINUATION',
        'database': '',
        'logger': '',
        'message': line,
        'raw': line
    }


@odoo_logs_bp.route('/available/<instance_name>', methods=['GET'])
@jwt_required()
def get_available_logs(instance_name):
    """Lista los archivos de log disponibles para una instancia"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role not in ['admin', 'developer', 'viewer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    base_path = _get_instance_log_path(instance_name)
    if not base_path:
        return jsonify({'error': f'Instancia no encontrada: {instance_name}'}), 404
    
    available = []
    
    # Buscar archivos .log en el directorio de la instancia
    if os.path.isdir(base_path):
        for f in sorted(os.listdir(base_path)):
            if f.endswith('.log'):
                filepath = os.path.join(base_path, f)
                size = os.path.getsize(filepath)
                available.append({
                    'name': f.replace('.log', ''),
                    'filename': f,
                    'size': size,
                    'size_human': _human_size(size)
                })
    
    # También verificar logs de systemd
    service_name = _get_service_name(instance_name)
    if service_name:
        available.append({
            'name': 'systemd',
            'filename': f'journalctl:{service_name}',
            'size': 0,
            'size_human': 'systemd'
        })
    
    return jsonify({
        'success': True,
        'instance': instance_name,
        'logs': available
    }), 200


@odoo_logs_bp.route('/view/<instance_name>', methods=['GET'])
@jwt_required()
def view_log(instance_name):
    """Lee y devuelve las últimas líneas de un archivo de log con parsing"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role not in ['admin', 'developer', 'viewer']:
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    base_path = _get_instance_log_path(instance_name)
    if not base_path:
        return jsonify({'error': f'Instancia no encontrada: {instance_name}'}), 404
    
    # Parámetros
    log_type = request.args.get('type', 'odoo')
    lines_count = request.args.get('lines', 500, type=int)
    level_filter = request.args.get('level', '')  # INFO, WARNING, ERROR, CRITICAL
    search = request.args.get('search', '')
    
    # Limitar líneas
    lines_count = min(lines_count, 5000)
    
    # Determinar archivo
    if log_type == 'systemd':
        return _read_systemd_log(instance_name, lines_count, level_filter, search)
    
    log_filename = f'{log_type}.log'
    log_path = os.path.join(base_path, log_filename)
    
    if not os.path.exists(log_path):
        return jsonify({
            'error': f'Archivo de log no encontrado: {log_filename}',
            'path': log_path
        }), 404
    
    # Leer últimas líneas
    raw_lines = tail_file(log_path, lines_count * 2 if level_filter else lines_count)
    
    # Parsear líneas
    parsed_lines = []
    for line in raw_lines:
        if not line.strip():
            continue
        parsed = parse_log_line(line)
        
        # Filtrar por nivel
        if level_filter and parsed['level'] not in ('CONTINUATION', level_filter):
            continue
        
        # Filtrar por búsqueda
        if search and search.lower() not in line.lower():
            continue
        
        parsed_lines.append(parsed)
    
    # Limitar resultado final
    parsed_lines = parsed_lines[-lines_count:]
    
    # Estadísticas
    stats = {
        'total': len(parsed_lines),
        'info': sum(1 for l in parsed_lines if l['level'] == 'INFO'),
        'warning': sum(1 for l in parsed_lines if l['level'] == 'WARNING'),
        'error': sum(1 for l in parsed_lines if l['level'] == 'ERROR'),
        'critical': sum(1 for l in parsed_lines if l['level'] == 'CRITICAL'),
        'debug': sum(1 for l in parsed_lines if l['level'] == 'DEBUG'),
    }
    
    # Info del archivo
    file_size = os.path.getsize(log_path)
    
    return jsonify({
        'success': True,
        'instance': instance_name,
        'log_type': log_type,
        'lines': parsed_lines,
        'stats': stats,
        'file_info': {
            'path': log_path,
            'size': file_size,
            'size_human': _human_size(file_size)
        }
    }), 200


def _read_systemd_log(instance_name, lines_count, level_filter, search):
    """Lee logs desde journalctl para una instancia"""
    import subprocess
    
    service_name = _get_service_name(instance_name)
    if not service_name:
        return jsonify({'error': 'Servicio systemd no encontrado'}), 404
    
    try:
        cmd = ['journalctl', '-u', service_name, '--no-pager', '-n', str(lines_count)]
        
        if level_filter:
            priority_map = {
                'ERROR': '3',
                'CRITICAL': '2',
                'WARNING': '4',
                'INFO': '6',
                'DEBUG': '7'
            }
            if level_filter in priority_map:
                cmd.extend(['-p', priority_map[level_filter]])
        
        if search:
            cmd.extend(['-g', search])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        lines = []
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            lines.append({
                'timestamp': '',
                'pid': '',
                'level': 'INFO',
                'database': '',
                'logger': 'systemd',
                'message': line,
                'raw': line
            })
        
        return jsonify({
            'success': True,
            'instance': instance_name,
            'log_type': 'systemd',
            'lines': lines,
            'stats': {'total': len(lines)},
            'file_info': {
                'path': f'journalctl -u {service_name}',
                'size': 0,
                'size_human': 'systemd'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error leyendo logs de systemd: {str(e)}'}), 500


def _human_size(size_bytes):
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
