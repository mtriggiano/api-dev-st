import os
import json
import subprocess
from datetime import datetime
import glob

class BackupManager:
    def __init__(self, backup_dir='/home/go/backups', scripts_path='/home/go/scripts'):
        self.backup_dir = backup_dir
        self.scripts_path = scripts_path
        self.config_file = os.path.join(backup_dir, 'backup_config.json')
        self._ensure_backup_dir()
        self._load_config()
    
    def _ensure_backup_dir(self):
        """Asegura que el directorio de backups existe"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _load_config(self):
        """Carga la configuración de backups"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Configuración por defecto
            self.config = {
                'retention_days': 7,
                'schedule': '0 3 * * *',  # 3 AM diario
                'auto_backup_enabled': True,
                'last_backup': None
            }
            self._save_config()
    
    def _save_config(self):
        """Guarda la configuración de backups"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_config(self):
        """Obtiene la configuración actual"""
        return self.config
    
    def update_config(self, retention_days=None, schedule=None, auto_backup_enabled=None):
        """Actualiza la configuración de backups"""
        if retention_days is not None:
            self.config['retention_days'] = int(retention_days)
        if schedule is not None:
            self.config['schedule'] = schedule
        if auto_backup_enabled is not None:
            self.config['auto_backup_enabled'] = bool(auto_backup_enabled)
        
        self._save_config()
        
        # Actualizar crontab si cambió el schedule
        if schedule is not None or auto_backup_enabled is not None:
            self._update_crontab()
        
        return {'success': True, 'config': self.config}
    
    def _update_crontab(self):
        """Actualiza el crontab con el schedule configurado"""
        script_path = os.path.join(self.scripts_path, 'backup-production.sh')
        cron_comment = "# Odoo Production Backup"
        
        # Leer crontab actual
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
        except:
            current_cron = ""
        
        # Eliminar líneas antiguas del backup
        lines = [line for line in current_cron.split('\n') 
                if cron_comment not in line and script_path not in line]
        
        # Agregar nueva línea si está habilitado
        if self.config['auto_backup_enabled']:
            lines.append(f"{cron_comment}")
            lines.append(f"{self.config['schedule']} {script_path} >> /home/go/backups/cron.log 2>&1")
        
        # Escribir nuevo crontab
        new_cron = '\n'.join(lines) + '\n'
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_cron)
    
    def create_backup(self):
        """Crea un nuevo backup"""
        script_path = os.path.join(self.scripts_path, 'backup-production.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de backup no encontrado'}
        
        try:
            # Ejecutar script en background
            cmd = f"RETENTION_DAYS={self.config['retention_days']} /bin/bash {script_path} > /tmp/odoo-backup-latest.log 2>&1 &"
            subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            return {
                'success': True,
                'message': 'Backup iniciado',
                'log_file': '/tmp/odoo-backup-latest.log'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def list_backups(self):
        """Lista todos los backups disponibles"""
        pattern = os.path.join(self.backup_dir, 'backup_*.tar.gz')
        backups = []
        
        for backup_file in sorted(glob.glob(pattern), reverse=True):
            try:
                # Leer metadatos si existen
                basename = os.path.basename(backup_file).replace('.tar.gz', '')
                
                # Extraer timestamp del nombre
                parts = basename.split('_')
                if len(parts) >= 3:
                    date_str = parts[2]
                    time_str = parts[3] if len(parts) > 3 else '000000'
                    timestamp = f"{date_str}_{time_str}"
                else:
                    timestamp = 'unknown'
                
                # Información del archivo
                stat = os.stat(backup_file)
                size_bytes = stat.st_size
                size_mb = size_bytes / (1024 * 1024)
                
                backups.append({
                    'filename': os.path.basename(backup_file),
                    'path': backup_file,
                    'timestamp': timestamp,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size_bytes': size_bytes,
                    'size_mb': round(size_mb, 2),
                    'size_human': self._human_readable_size(size_bytes)
                })
            except Exception as e:
                print(f"Error reading backup {backup_file}: {e}")
                continue
        
        # Calcular estadísticas
        total_size = sum(b['size_bytes'] for b in backups)
        
        return {
            'backups': backups,
            'count': len(backups),
            'total_size_bytes': total_size,
            'total_size_human': self._human_readable_size(total_size),
            'retention_days': self.config['retention_days']
        }
    
    def delete_backup(self, filename):
        """Elimina un backup específico"""
        backup_path = os.path.join(self.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup no encontrado'}
        
        if not filename.startswith('backup_') or not filename.endswith('.tar.gz'):
            return {'success': False, 'error': 'Nombre de archivo inválido'}
        
        try:
            os.remove(backup_path)
            return {'success': True, 'message': f'Backup {filename} eliminado'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_backup_log(self):
        """Obtiene el log del último backup"""
        log_file = '/tmp/odoo-backup-latest.log'
        
        if not os.path.exists(log_file):
            return {'log': 'No hay log disponible', 'exists': False}
        
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            return {'log': log_content, 'exists': True}
        except Exception as e:
            return {'log': f'Error al leer log: {str(e)}', 'exists': False}
    
    @staticmethod
    def _human_readable_size(size_bytes):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
