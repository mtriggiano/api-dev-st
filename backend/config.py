import os
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

# Cargar .env desde la raíz del proyecto
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER', 'go')}:{os.getenv('DB_PASSWORD', '!Phax3312!IMAC')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'server_panel')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Server paths - Actualizados para nueva estructura
    PROJECT_ROOT = os.getenv('PROJECT_ROOT', '/home/go/api-dev')
    PROD_ROOT = os.getenv('PROD_ROOT', '/home/go/apps/production/odoo')
    DEV_ROOT = os.getenv('DEV_ROOT', '/home/go/apps/develop/odoo')
    SCRIPTS_PATH = os.getenv('SCRIPTS_PATH', f'{PROJECT_ROOT}/scripts')
    DATA_PATH = os.getenv('DATA_PATH', f'{PROJECT_ROOT}/data')
    PUERTOS_FILE = os.getenv('PUERTOS_FILE', f'{DATA_PATH}/puertos_ocupados_odoo.txt')
    DEV_INSTANCES_FILE = os.getenv('DEV_INSTANCES_FILE', f'{DATA_PATH}/dev-instances.txt')
    BACKUPS_PATH = os.getenv('BACKUPS_PATH', '/home/go/backups')
    
    # Domain configuration - IMPORTANTE: El dominio raíz está protegido
    DOMAIN_ROOT = os.getenv('DOMAIN_ROOT', 'softrigx.com')
    PUBLIC_IP = os.getenv('PUBLIC_IP', '')
    
    # CORS - Dinámico basado en dominio configurado
    API_DOMAIN = os.getenv('API_DOMAIN', 'api-dev.hospitalprivadosalta.ar')
    API_BASE_URL = os.getenv('API_BASE_URL', f'https://{API_DOMAIN}')
    CORS_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:3000',
        f'https://{API_DOMAIN}',
        f'http://{API_DOMAIN}'
    ]
    
    # GitHub OAuth (opcional - para futuras mejoras con OAuth flow)
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:5173/auth/github/callback')
