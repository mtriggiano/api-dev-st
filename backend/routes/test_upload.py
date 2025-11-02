from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

test_upload_bp = Blueprint('test_upload', __name__)

@test_upload_bp.route('/test-upload', methods=['POST'])
@jwt_required()
def test_upload():
    """Endpoint de prueba para uploads grandes"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Solo guardar en /tmp para probar
        temp_path = f"/tmp/test_{file.filename}"
        file.save(temp_path)
        
        size = os.path.getsize(temp_path)
        
        # Limpiar
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
