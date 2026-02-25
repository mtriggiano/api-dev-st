import os
import subprocess
import requests
import logging
import re
from typing import Dict, List, Optional
from flask import current_app
from urllib.parse import urlparse, urlunparse

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
    
    def _convert_to_ssh_url(self, url: str) -> str:
        """Convierte una URL HTTPS de GitHub a SSH"""
        if url.startswith('https://github.com/'):
            # https://github.com/user/repo.git -> git@github.com:user/repo.git
            path = url.replace('https://github.com/', '')
            return f'git@github.com:{path}'
        return url
    
    def _clean_url(self, url: str) -> str:
        """Limpia una URL removiendo credenciales embebidas"""
        # Remover cualquier credencial existente en la URL
        # https://token@github.com/user/repo.git -> https://github.com/user/repo.git
        # https://user:pass@github.com/user/repo.git -> https://github.com/user/repo.git
        cleaned = re.sub(r'https://[^@]+@', 'https://', url)
        return cleaned
    
    def _add_token_to_url(self, url: str, token: str) -> str:
        """Agrega un token a una URL HTTPS de forma segura"""
        # Primero limpiar la URL de cualquier credencial existente
        clean_url = self._clean_url(url)
        
        # Validar que sea una URL HTTPS válida
        if not clean_url.startswith('https://'):
            return clean_url
        
        # Parsear la URL
        parsed = urlparse(clean_url)
        
        # Validar que tenga un hostname válido
        if not parsed.netloc or '/' in parsed.netloc:
            logger.error(f"URL inválida detectada: {clean_url}")
            return clean_url
        
        # Construir nueva URL con token
        # https://github.com -> https://TOKEN@github.com
        new_netloc = f"{token}@{parsed.netloc}"
        new_parsed = parsed._replace(netloc=new_netloc)
        
        return urlunparse(new_parsed)
    
    def _run_git_command(self, command: List[str], cwd: str) -> Dict:
        """Ejecuta un comando git y retorna el resultado"""
        try:
            # Usar ruta completa de git para evitar problemas de PATH
            if command[0] == 'git':
                command[0] = '/usr/bin/git'
            
            # Configurar entorno para que Git encuentre SSH
            env = os.environ.copy()
            env['GIT_SSH_COMMAND'] = '/usr/bin/ssh -o StrictHostKeyChecking=no'
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60,
                env=env
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
    
    def init_git_repo(self, local_path: str, repo_url: str, branch: str = 'main', token: str = None) -> Dict:
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
        
        # Siempre usar la URL limpia sin token para el remote
        # El token se manejará temporalmente en cada operación (pull/push)
        logger.info(f'Configurando remote con URL: {repo_url}')
        
        # Agregar remote sin token
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
        """Hace push de los commits al repositorio remoto. Si falla por non-fast-forward, hace pull --no-rebase y reintenta."""
        if not os.path.exists(os.path.join(local_path, '.git')):
            return {'success': False, 'error': 'No es un repositorio Git'}
        
        # Si hay token, configurar credential helper
        original_url = None
        if token:
            # Configurar token temporalmente
            remote_result = self._run_git_command(['git', 'remote', 'get-url', 'origin'], local_path)
            if remote_result['success'] and remote_result['stdout'].startswith('https://'):
                # Actualizar URL con token de forma segura
                original_url = remote_result['stdout']
                auth_url = self._add_token_to_url(original_url, token)
                if auth_url != original_url:  # Solo actualizar si cambió
                    self._run_git_command(['git', 'remote', 'set-url', 'origin', auth_url], local_path)
        
        try:
            # Push
            if branch:
                push_result = self._run_git_command(['git', 'push', 'origin', branch], local_path)
            else:
                push_result = self._run_git_command(['git', 'push'], local_path)
            
            # Si falla por non-fast-forward, hacer pull --no-rebase y reintentar
            if not push_result['success'] and 'non-fast-forward' in push_result.get('stderr', ''):
                # Auto-pull
                if branch:
                    pull_result = self._run_git_command(['git', 'pull', '--no-rebase', 'origin', branch], local_path)
                else:
                    pull_result = self._run_git_command(['git', 'pull', '--no-rebase'], local_path)
                
                if not pull_result['success']:
                    return {
                        'success': False,
                        'error': f'Error al hacer auto-pull antes de push: {pull_result.get("stderr")}'
                    }
                
                # Reintentar push
                if branch:
                    push_result = self._run_git_command(['git', 'push', 'origin', branch], local_path)
                else:
                    push_result = self._run_git_command(['git', 'push'], local_path)
                
                if push_result['success']:
                    return {
                        'success': True,
                        'message': 'Push exitoso (auto-pull realizado)',
                        'warning': 'Se hizo pull automático antes de push porque la rama remota tenía cambios nuevos',
                        'output': push_result['stderr']
                    }
            
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
        finally:
            # Restaurar URL original si se modificó
            if token and original_url:
                self._run_git_command(['git', 'remote', 'set-url', 'origin', original_url], local_path)
    
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
                auth_url = self._add_token_to_url(original_url, token)
                if auth_url != original_url:  # Solo actualizar si cambió
                    self._run_git_command(['git', 'remote', 'set-url', 'origin', auth_url], local_path)
        
        # Verificar si la rama existe en el remoto
        if branch:
            ls_remote = self._run_git_command(['git', 'ls-remote', '--heads', 'origin', branch], local_path)
            branch_exists = ls_remote['success'] and ls_remote['stdout'].strip()
            
            if not branch_exists:
                # La rama no existe en el remoto, crearla basada en main si existe
                logger.info(f"Branch {branch} no existe en remoto, creando con push inicial")
                
                # Verificar si existe la rama main en el remoto
                main_remote = self._run_git_command(['git', 'ls-remote', '--heads', 'origin', 'main'], local_path)
                main_exists = main_remote['success'] and main_remote['stdout'].strip()
                
                if main_exists:
                    # Main existe, hacer fetch y crear rama basada en main
                    logger.info(f"Rama main existe en remoto, creando {branch} basada en main")
                    self._run_git_command(['git', 'fetch', 'origin', 'main'], local_path)
                    # Crear rama basada en origin/main
                    self._run_git_command(['git', 'checkout', '-b', branch, 'origin/main'], local_path)
                else:
                    # Main no existe, crear rama desde cero
                    logger.info(f"Rama main no existe, creando {branch} desde cero")
                    self._run_git_command(['git', 'checkout', '-B', branch], local_path)
                    
                    # Verificar si hay commits en la rama
                    log_result = self._run_git_command(['git', 'log', '--oneline', '-1'], local_path)
                    has_commits = log_result['success'] and log_result['stdout'].strip()
                    
                    if not has_commits:
                        # No hay commits, verificar si hay archivos para commitear
                        status = self._run_git_command(['git', 'status', '--porcelain'], local_path)
                        if status['success'] and status['stdout'].strip():
                            # Hay archivos sin commitear
                            self._run_git_command(['git', 'add', '.'], local_path)
                            self._run_git_command(['git', 'commit', '-m', 'Initial commit from local files'], local_path)
                        else:
                            # No hay archivos, crear commit vacío
                            self._run_git_command(['git', 'commit', '--allow-empty', '-m', 'Initial empty commit'], local_path)
                
                # Push inicial
                push_result = self._run_git_command(['git', 'push', '-u', 'origin', branch], local_path)
                
                # Restaurar URL original si se modificó
                if token and original_url:
                    self._run_git_command(['git', 'remote', 'set-url', 'origin', original_url], local_path)
                
                if push_result['success']:
                    return {
                        'success': True,
                        'message': f'Rama {branch} creada en remoto',
                        'output': push_result['stdout']
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error al crear rama en remoto: {push_result.get("stderr")}'
                    }
        
        # Configurar estrategia de pull (merge por defecto)
        self._run_git_command(['git', 'config', 'pull.rebase', 'false'], local_path)
        
        # Pull normal con estrategia de merge
        if branch:
            pull_result = self._run_git_command(['git', 'pull', 'origin', branch, '--no-rebase'], local_path)
        else:
            pull_result = self._run_git_command(['git', 'pull', '--no-rebase'], local_path)
        
        # Si falla por historias no relacionadas, intentar con --allow-unrelated-histories
        if not pull_result['success'] and 'unrelated histories' in pull_result.get('stderr', ''):
            logger.info("Detectado error de historias no relacionadas, reintentando con --allow-unrelated-histories")
            if branch:
                pull_result = self._run_git_command(['git', 'pull', 'origin', branch, '--no-rebase', '--allow-unrelated-histories'], local_path)
            else:
                pull_result = self._run_git_command(['git', 'pull', '--no-rebase', '--allow-unrelated-histories'], local_path)
        
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
    
    def get_remote_branches(self, local_path: str) -> Dict:
        """Obtiene las ramas disponibles del repositorio remoto"""
        
        if not local_path or not os.path.exists(local_path):
            return {
                'success': False,
                'error': 'La ruta local del repositorio no existe'
            }
        
        # Obtener ramas remotas usando git ls-remote
        result = self._run_git_command(['git', 'ls-remote', '--heads', 'origin'], local_path)
        
        if not result['success']:
            return {
                'success': False,
                'error': f'Error al obtener ramas remotas: {result.get("stderr")}'
            }
        
        # Parsear la salida de ls-remote
        # Formato: <hash>\trefs/heads/<branch_name>
        branches = []
        for line in result['stdout'].strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) == 2:
                    ref = parts[1]
                    if ref.startswith('refs/heads/'):
                        branch_name = ref.replace('refs/heads/', '')
                        branches.append(branch_name)
        
        return {
            'success': True,
            'branches': branches
        }
