import os
import subprocess
import requests
import logging
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class GitManager:
    """Gestor de operaciones Git y GitHub API"""
    
    GITHUB_API_BASE = "https://api.github.com"
    
    def __init__(self):
        self.dev_root = None
    
    def _init_paths(self):
        """Inicializa las rutas desde la configuración"""
        if not self.dev_root:
            self.dev_root = current_app.config['DEV_ROOT']
    
    def _run_git_command(self, command: List[str], cwd: str) -> Dict:
        """Ejecuta un comando git y retorna el resultado"""
        try:
            # Usar ruta completa de git para evitar problemas de PATH
            if command[0] == 'git':
                command[0] = '/usr/bin/git'
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Comando Git excedió el tiempo límite'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _github_api_request(self, endpoint: str, token: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Realiza una petición a la API de GitHub"""
        url = f"{self.GITHUB_API_BASE}{endpoint}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return {'success': False, 'error': 'Método HTTP no soportado'}
            
            if response.status_code in [200, 201, 204]:
                return {
                    'success': True,
                    'data': response.json() if response.content else None
                }
            else:
                return {
                    'success': False,
                    'error': f'GitHub API error: {response.status_code}',
                    'message': response.json().get('message', 'Unknown error') if response.content else 'No response'
                }
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Timeout al conectar con GitHub API'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def verify_github_token(self, token: str) -> Dict:
        """Verifica que el token de GitHub sea válido y obtiene info del usuario"""
        result = self._github_api_request('/user', token)
        
        if result['success']:
            user_data = result['data']
            return {
                'success': True,
                'username': user_data.get('login'),
                'name': user_data.get('name'),
                'email': user_data.get('email'),
                'avatar_url': user_data.get('avatar_url')
            }
        else:
            return result
    
    def list_user_repos(self, token: str) -> Dict:
        """Lista los repositorios del usuario"""
        result = self._github_api_request('/user/repos?per_page=100&sort=updated', token)
        
        if result['success']:
            repos = result['data']
            return {
                'success': True,
                'repos': [{
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'owner': repo['owner']['login'],
                    'private': repo['private'],
                    'default_branch': repo['default_branch'],
                    'clone_url': repo['clone_url'],
                    'ssh_url': repo['ssh_url'],
                    'updated_at': repo['updated_at']
                } for repo in repos]
            }
        else:
            return result
    
    def init_git_repo(self, local_path: str, repo_url: str, branch: str = 'main') -> Dict:
        """Inicializa un repositorio Git en la carpeta local"""
        if not os.path.exists(local_path):
            return {'success': False, 'error': f'La ruta {local_path} no existe'}
        
        # Verificar si ya es un repo git
        git_dir = os.path.join(local_path, '.git')
        if os.path.exists(git_dir):
            return {'success': False, 'error': 'La carpeta ya es un repositorio Git'}
        
        # Inicializar repo
        result = self._run_git_command(['git', 'init'], local_path)
        if not result['success']:
            error_msg = result.get('stderr') or result.get('error') or 'Error desconocido'
            return {'success': False, 'error': f'Error al inicializar repo: {error_msg}'}
        
        # Configurar usuario Git (necesario para commits)
        self._run_git_command(['git', 'config', 'user.name', 'API Dev Panel'], local_path)
        self._run_git_command(['git', 'config', 'user.email', 'dev@panel.local'], local_path)
        
        # Agregar remote
        result = self._run_git_command(['git', 'remote', 'add', 'origin', repo_url], local_path)
        if not result['success']:
            return {'success': False, 'error': f'Error al agregar remote: {result.get("stderr")}'}
        
        # Configurar branch
        result = self._run_git_command(['git', 'branch', '-M', branch], local_path)
        if not result['success']:
            logger.warning(f'No se pudo configurar branch: {result.get("stderr")}')
        
        return {
            'success': True,
            'message': f'Repositorio inicializado en {local_path}'
        }
    
    def clone_repo(self, repo_url: str, local_path: str, branch: str = 'main', token: str = None) -> Dict:
        """Clona un repositorio en la carpeta local"""
        if os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'La carpeta ya contiene un repositorio Git'}
        
        # Si hay token, incluirlo en la URL para autenticación
        if token and repo_url.startswith('https://'):
            repo_url = repo_url.replace('https://', f'https://{token}@')
        
        command = ['git', 'clone', '-b', branch, repo_url, local_path]
        result = self._run_git_command(command, os.path.dirname(local_path))
        
        if result['success']:
            return {
                'success': True,
                'message': f'Repositorio clonado en {local_path}'
            }
        else:
            return {
                'success': False,
                'error': f'Error al clonar: {result.get("stderr")}'
            }
    
    def get_repo_status(self, local_path: str) -> Dict:
        """Obtiene el estado del repositorio Git"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Status
        status_result = self._run_git_command(['git', 'status', '--porcelain'], local_path)
        
        # Branch actual
        branch_result = self._run_git_command(['git', 'branch', '--show-current'], local_path)
        
        # Último commit
        log_result = self._run_git_command(
            ['git', 'log', '-1', '--pretty=format:%H|%an|%ae|%at|%s'],
            local_path
        )
        
        # Remote URL
        remote_result = self._run_git_command(['git', 'remote', 'get-url', 'origin'], local_path)
        
        last_commit = None
        if log_result['success'] and log_result['stdout']:
            parts = log_result['stdout'].split('|')
            if len(parts) == 5:
                last_commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'timestamp': parts[3],
                    'message': parts[4]
                }
        
        # Parsear cambios
        changes = []
        if status_result['success'] and status_result['stdout']:
            for line in status_result['stdout'].split('\n'):
                if line.strip():
                    status_code = line[:2]
                    filename = line[3:]
                    changes.append({
                        'status': status_code.strip(),
                        'file': filename
                    })
        
        return {
            'success': True,
            'branch': branch_result['stdout'] if branch_result['success'] else 'unknown',
            'remote_url': remote_result['stdout'] if remote_result['success'] else None,
            'has_changes': bool(changes),
            'changes': changes,
            'last_commit': last_commit
        }
    
    def commit_changes(self, local_path: str, message: str, author_name: str = None, author_email: str = None) -> Dict:
        """Crea un commit con los cambios actuales"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Configurar autor si se proporciona
        if author_name:
            self._run_git_command(['git', 'config', 'user.name', author_name], local_path)
        if author_email:
            self._run_git_command(['git', 'config', 'user.email', author_email], local_path)
        
        # Add all
        add_result = self._run_git_command(['git', 'add', '.'], local_path)
        if not add_result['success']:
            return {'success': False, 'error': f'Error al agregar archivos: {add_result.get("stderr")}'}
        
        # Commit
        commit_result = self._run_git_command(['git', 'commit', '-m', message], local_path)
        
        if commit_result['success']:
            return {
                'success': True,
                'message': 'Commit creado exitosamente',
                'output': commit_result['stdout']
            }
        elif 'nothing to commit' in commit_result['stdout']:
            return {
                'success': False,
                'error': 'No hay cambios para commitear'
            }
        else:
            return {
                'success': False,
                'error': f'Error al crear commit: {commit_result.get("stderr")}'
            }
    
    def push_changes(self, local_path: str, branch: str = None, token: str = None) -> Dict:
        """Hace push de los commits al repositorio remoto"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Si hay token, configurar credential helper
        original_url = None
        if token:
            # Configurar token temporalmente
            remote_result = self._run_git_command(['git', 'remote', 'get-url', 'origin'], local_path)
            if remote_result['success'] and remote_result['stdout'].startswith('https://'):
                # Actualizar URL con token
                original_url = remote_result['stdout']
                auth_url = original_url.replace('https://', f'https://{token}@')
                self._run_git_command(['git', 'remote', 'set-url', 'origin', auth_url], local_path)
        
        # Push
        if branch:
            push_result = self._run_git_command(['git', 'push', 'origin', branch], local_path)
        else:
            push_result = self._run_git_command(['git', 'push'], local_path)
        
        # Restaurar URL original si se modificó
        if token and original_url:
            self._run_git_command(['git', 'remote', 'set-url', 'origin', original_url], local_path)
        
        if push_result['success']:
            return {
                'success': True,
                'message': 'Push exitoso',
                'output': push_result['stderr']  # Git push usa stderr para output
            }
        else:
            return {
                'success': False,
                'error': f'Error al hacer push: {push_result.get("stderr")}'
            }
    
    def pull_changes(self, local_path: str, branch: str = None, token: str = None) -> Dict:
        """Hace pull de los cambios del repositorio remoto"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Si hay token, configurar credential helper
        original_url = None
        if token:
            remote_result = self._run_git_command(['git', 'remote', 'get-url', 'origin'], local_path)
            if remote_result['success'] and remote_result['stdout'].startswith('https://'):
                original_url = remote_result['stdout']
                auth_url = original_url.replace('https://', f'https://{token}@')
                self._run_git_command(['git', 'remote', 'set-url', 'origin', auth_url], local_path)
        
        # Pull
        if branch:
            pull_result = self._run_git_command(['git', 'pull', 'origin', branch], local_path)
        else:
            pull_result = self._run_git_command(['git', 'pull'], local_path)
        
        # Restaurar URL original si se modificó
        if token and original_url:
            self._run_git_command(['git', 'remote', 'set-url', 'origin', original_url], local_path)
        
        if pull_result['success']:
            return {
                'success': True,
                'message': 'Pull exitoso',
                'output': pull_result['stdout']
            }
        else:
            return {
                'success': False,
                'error': f'Error al hacer pull: {pull_result.get("stderr")}'
            }
    
    def get_commit_history(self, local_path: str, limit: int = 20) -> Dict:
        """Obtiene el historial de commits"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        result = self._run_git_command(
            ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ae|%at|%s'],
            local_path
        )
        
        if not result['success']:
            return {'success': False, 'error': 'Error al obtener historial'}
        
        commits = []
        if result['stdout']:
            for line in result['stdout'].split('\n'):
                parts = line.split('|')
                if len(parts) == 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'timestamp': parts[3],
                        'message': parts[4]
                    })
        
        return {
            'success': True,
            'commits': commits
        }
    
    def get_file_diff(self, local_path: str, file_path: str = None) -> Dict:
        """Obtiene el diff de archivos modificados"""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        if file_path:
            result = self._run_git_command(['git', 'diff', file_path], local_path)
        else:
            result = self._run_git_command(['git', 'diff'], local_path)
        
        if result['success']:
            return {
                'success': True,
                'diff': result['stdout']
            }
        else:
            return {
                'success': False,
                'error': f'Error al obtener diff: {result.get("stderr")}'
            }
