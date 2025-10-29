from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db, User
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensiones
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt = JWTManager(app)
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.metrics import metrics_bp
    from routes.instances import instances_bp
    from routes.logs import logs_bp
    from routes.backup import backup_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(metrics_bp, url_prefix='/api/metrics')
    app.register_blueprint(instances_bp, url_prefix='/api/instances')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(backup_bp, url_prefix='/api/backup')
    
    # Manejadores de errores JWT
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token expirado'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Token inválido'}), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Token no proporcionado'}), 401
    
    # Ruta de health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'server-panel-api'}), 200
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Server Panel API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'metrics': '/api/metrics',
                'instances': '/api/instances',
                'logs': '/api/logs',
                'backup': '/api/backup'
            }
        }), 200
    
    return app

def init_db(app):
    """Inicializa la base de datos y crea usuario admin por defecto"""
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin si no existe
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')  # Cambiar después del primer login
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado (usuario: admin, contraseña: admin123)")
        else:
            print("✅ Usuario admin ya existe")

if __name__ == '__main__':
    app = create_app()
    
    # Inicializar BD
    init_db(app)
    
    # Ejecutar en modo desarrollo
    app.run(host='0.0.0.0', port=5000, debug=True)
