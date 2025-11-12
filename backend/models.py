from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # admin, developer, viewer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ActionLog(db.Model):
    __tablename__ = 'action_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # create_instance, delete_instance, update_db, etc.
    instance_name = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)
    status = db.Column(db.String(20), default='success')  # success, error
    
    user = db.relationship('User', backref='actions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'action': self.action,
            'instance_name': self.instance_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'details': self.details,
            'status': self.status
        }

class GitHubConfig(db.Model):
    __tablename__ = 'github_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instance_name = db.Column(db.String(100), nullable=False)
    
    # GitHub OAuth
    github_username = db.Column(db.String(100))
    github_access_token = db.Column(db.String(255))  # Encrypted in production
    
    # Repository config
    repo_owner = db.Column(db.String(100))  # Usuario/Org dueño del repo
    repo_name = db.Column(db.String(100))   # Nombre del repositorio
    repo_branch = db.Column(db.String(100), default='main')  # Rama principal
    
    # Local path
    local_path = db.Column(db.String(500))  # Ruta a la carpeta custom addons
    
    # Instance type and deployment
    instance_type = db.Column(db.String(20), default='development')  # 'development' o 'production'
    auto_deploy = db.Column(db.Boolean, default=False)  # Auto-deploy en push a main
    webhook_secret = db.Column(db.String(100))  # Secret para validar webhook
    update_modules_on_deploy = db.Column(db.Boolean, default=False)  # Actualizar módulos Odoo
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_deploy_at = db.Column(db.DateTime)  # Último deploy automático
    
    user = db.relationship('User', backref='github_configs')
    
    # Unique constraint: un usuario solo puede tener una config por instancia
    __table_args__ = (db.UniqueConstraint('user_id', 'instance_name', name='_user_instance_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'instance_name': self.instance_name,
            'github_username': self.github_username,
            'repo_owner': self.repo_owner,
            'repo_name': self.repo_name,
            'repo_branch': self.repo_branch,
            'local_path': self.local_path,
            'instance_type': self.instance_type,
            'auto_deploy': self.auto_deploy,
            'update_modules_on_deploy': self.update_modules_on_deploy,
            'has_webhook': bool(self.webhook_secret),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_deploy_at': self.last_deploy_at.isoformat() if self.last_deploy_at else None,
            'is_active': self.is_active,
            'has_token': bool(self.github_access_token)
        }
    
    def is_production(self):
        """Verifica si la instancia es de producción"""
        return self.instance_type == 'production' or not self.instance_name.startswith('dev-')
    
    def get_default_branch(self):
        """Retorna la rama por defecto según el tipo de instancia"""
        if self.is_production():
            return 'main'
        else:
            return self.instance_name  # dev-mtg, dev-test, etc.

class MetricsHistory(db.Model):
    __tablename__ = 'metrics_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    cpu_percent = db.Column(db.Float)
    ram_percent = db.Column(db.Float)
    ram_used_gb = db.Column(db.Float)
    ram_total_gb = db.Column(db.Float)
    disk_percent = db.Column(db.Float)
    disk_used_gb = db.Column(db.Float)
    disk_total_gb = db.Column(db.Float)
    network_sent_mb = db.Column(db.Float)
    network_recv_mb = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_percent': self.cpu_percent,
            'ram_percent': self.ram_percent,
            'ram_used_gb': self.ram_used_gb,
            'ram_total_gb': self.ram_total_gb,
            'disk_percent': self.disk_percent,
            'disk_used_gb': self.disk_used_gb,
            'disk_total_gb': self.disk_total_gb,
            'network_sent_mb': self.network_sent_mb,
            'network_recv_mb': self.network_recv_mb
        }
