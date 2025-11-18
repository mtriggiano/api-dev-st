from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
import os
import hashlib

from config import Config

chunked_upload_bp = Blueprint('chunked_upload', __name__)

# Almacenamiento temporal de chunks
UPLOAD_FOLDER = '/tmp/chunked_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@chunked_upload_bp.route('/chunked-upload', methods=['POST'])
@jwt_required()
def chunked_upload():
    """Upload de archivos en chunks para evitar límites"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'error': 'Permisos insuficientes'}), 403
    
    try:
        # Obtener datos del chunk
        chunk = request.files.get('chunk')
        chunk_number = int(request.form.get('chunkNumber', 0))
        total_chunks = int(request.form.get('totalChunks', 1))
        file_name = request.form.get('fileName', 'unknown')
        file_id = request.form.get('fileId')  # ID único para el archivo
        
        if not chunk or not file_id:
            return jsonify({'error': 'Datos incompletos'}), 400
        
        # Crear directorio para este archivo
        file_dir = os.path.join(UPLOAD_FOLDER, file_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # Guardar chunk
        chunk_path = os.path.join(file_dir, f'chunk_{chunk_number}')
        chunk.save(chunk_path)
        
        # Si es el último chunk, ensamblar el archivo
        if chunk_number == total_chunks - 1:
            final_path = os.path.join(Config.BACKUPS_PATH, file_name)
            
            # Ensamblar todos los chunks
            with open(final_path, 'wb') as final_file:
                for i in range(total_chunks):
                    chunk_file = os.path.join(file_dir, f'chunk_{i}')
                    with open(chunk_file, 'rb') as cf:
                        final_file.write(cf.read())
                    os.remove(chunk_file)  # Limpiar chunk
            
            # Limpiar directorio temporal
            os.rmdir(file_dir)
            
            # Obtener tamaño
            size = os.path.getsize(final_path)
            
            return jsonify({
                'success': True,
                'message': 'Archivo ensamblado exitosamente',
                'fileName': file_name,
                'size': size,
                'complete': True
            }), 200
        
        return jsonify({
            'success': True,
            'message': f'Chunk {chunk_number + 1}/{total_chunks} recibido',
            'complete': False
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chunked_upload_bp.route('/chunked-upload/cancel', methods=['POST'])
@jwt_required()
def cancel_chunked_upload():
    """Cancelar upload y limpiar chunks"""
    try:
        file_id = request.json.get('fileId')
        if file_id:
            file_dir = os.path.join(UPLOAD_FOLDER, file_id)
            if os.path.exists(file_dir):
                import shutil
                shutil.rmtree(file_dir)
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
