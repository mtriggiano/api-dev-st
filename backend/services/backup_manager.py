import os
import json
import subprocess
from datetime import datetime
import glob
import logging

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BackupManager:
    def __init__(self, backup_dir='/home/go/backups', scripts_path='/home/go/api-dev/scripts'):
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
        script_path = os.path.join(self.scripts_path, 'odoo/backup-production.sh')
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
        script_path = os.path.join(self.scripts_path, 'odoo/backup-production.sh')
        
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
    
    def restore_backup(self, filename):
        """Restaura un backup de producción"""
        backup_path = os.path.join(self.backup_dir, filename)
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup no encontrado'}
        
        if not filename.startswith('backup_') or not filename.endswith('.tar.gz'):
            return {'success': False, 'error': 'Nombre de archivo inválido'}
        
        script_path = os.path.join(self.scripts_path, 'odoo/restore-production.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de restauración no encontrado'}
        
        try:
            # Ejecutar script de restauración en background
            cmd = f"/bin/bash {script_path} {filename} > /tmp/odoo-restore-latest.log 2>&1 &"
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
                'message': 'Restauración iniciada',
                'log_file': '/tmp/odoo-restore-latest.log',
                'backup_file': filename
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_restore_log(self):
        """Obtiene el log de la última restauración"""
        log_file = '/tmp/odoo-restore-latest.log'
        
        if not os.path.exists(log_file):
            return {'log': 'No hay log de restauración disponible', 'exists': False}
        
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            return {'log': log_content, 'exists': True}
        except Exception as e:
            return {'log': f'Error al leer log: {str(e)}', 'exists': False}
    
    def upload_backup(self, file):
        """Sube un archivo de backup (.tar.gz o .zip)"""
        import tarfile
        import zipfile
        import tempfile
        import shutil
        import sys
        
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 BACKUP_MANAGER: Iniciando upload de archivo: {file.filename}")
            logger.info(f"🔍 Tipo de objeto file: {type(file)}")
            logger.info(f"🔍 Atributos del file: {dir(file)}")
            sys.stdout.flush()
            
            # Generar nombre único con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = file.filename
            is_zip = original_filename.endswith('.zip')
            
            logger.info(f"📝 Tipo de archivo: {'ZIP' if is_zip else 'TAR.GZ'}")
            
            # Guardar archivo temporal
            temp_path = os.path.join(tempfile.gettempdir(), f"upload_{timestamp}_{original_filename}")
            
            logger.info(f"💾 Guardando en: {temp_path}")
            sys.stdout.flush()
            
            # Guardar el archivo directamente (stream-safe)
            logger.info("📥 Guardando archivo por chunks (stream-safe)...")
            sys.stdout.flush()
            with open(temp_path, "wb") as f:
                chunk_size = 8192
                while True:
                    chunk = file.stream.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
            logger.info("✅ Archivo guardado completamente (stream-safe)")
            sys.stdout.flush()
            
            # Obtener tamaño del archivo guardado
            bytes_written = os.path.getsize(temp_path)
            
            logger.info(f"✅ Archivo guardado completamente: {bytes_written / 1024 / 1024:.2f}MB")
            sys.stdout.flush()
            
            # Si es ZIP, convertir a TAR.GZ
            if is_zip:
                logger.info("📂 Iniciando conversión de ZIP a TAR.GZ...")
                
                # Crear directorio temporal para extraer
                extract_dir = os.path.join(tempfile.gettempdir(), f"extract_{timestamp}")
                os.makedirs(extract_dir, exist_ok=True)
                logger.info(f"📁 Directorio de extracción: {extract_dir}")
                
                try:
                    # Extraer ZIP
                    logger.info("🔓 Extrayendo archivo ZIP...")
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    logger.info("✅ Extracción completada")
                    
                    # Validar estructura
                    logger.info("🔍 Validando estructura del backup...")
                    has_dump = False
                    has_filestore = False
                    
                    for root, dirs, files in os.walk(extract_dir):
                        if 'dump.sql' in files:
                            has_dump = True
                            logger.info(f"✅ dump.sql encontrado en: {root}")
                        if 'filestore' in dirs:
                            has_filestore = True
                            logger.info(f"✅ filestore encontrado en: {root}")
                    
                    if not has_dump:
                        logger.error("❌ El backup no contiene dump.sql")
                        shutil.rmtree(extract_dir)
                        os.remove(temp_path)
                        return {'success': False, 'error': 'El backup no contiene dump.sql'}
                    
                    if not has_filestore:
                        logger.warning("⚠️ El backup no contiene filestore")
                    
                    # Crear TAR.GZ desde el contenido extraído
                    logger.info("📦 Creando archivo TAR.GZ...")
                    final_filename = f"backup_production_{timestamp}.tar.gz"
                    final_filepath = os.path.join(self.backup_dir, final_filename)
                    
                    with tarfile.open(final_filepath, 'w:gz') as tar:
                        for item in os.listdir(extract_dir):
                            logger.info(f"➕ Agregando: {item}")
                            tar.add(os.path.join(extract_dir, item), arcname=item)
                    
                    logger.info(f"✅ TAR.GZ creado: {final_filepath}")
                    
                    # Limpiar temporales
                    logger.info("🧹 Limpiando archivos temporales...")
                    shutil.rmtree(extract_dir)
                    os.remove(temp_path)
                    logger.info("✅ Archivos temporales eliminados")
                    
                except Exception as e:
                    if os.path.exists(extract_dir):
                        shutil.rmtree(extract_dir)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise e
                    
            else:
                # Es TAR.GZ, mover directamente
                logger.info("📦 Procesando archivo TAR.GZ...")
                final_filename = f"backup_production_{timestamp}.tar.gz"
                final_filepath = os.path.join(self.backup_dir, final_filename)
                logger.info(f"📁 Moviendo a: {final_filepath}")
                shutil.move(temp_path, final_filepath)
                
                # Validar que es un tar.gz válido
                logger.info("🔍 Validando formato TAR.GZ...")
                if not tarfile.is_tarfile(final_filepath):
                    logger.error("❌ El archivo no es un tar.gz válido")
                    os.remove(final_filepath)
                    return {'success': False, 'error': 'El archivo no es un tar.gz válido'}
                
                # Validar estructura interna
                logger.info("🔍 Validando estructura interna...")
                with tarfile.open(final_filepath, 'r:gz') as tar:
                    members = tar.getnames()
                    logger.info(f"📋 Archivos en el TAR: {len(members)} elementos")
                    
                    has_dump = any('dump.sql' in m for m in members)
                    has_filestore = any('filestore' in m for m in members)
                    
                    if has_dump:
                        logger.info("✅ dump.sql encontrado")
                    if has_filestore:
                        logger.info("✅ filestore encontrado")
                    
                    if not has_dump:
                        logger.error("❌ El backup no contiene dump.sql")
                        os.remove(final_filepath)
                        return {'success': False, 'error': 'El backup no contiene dump.sql'}
                    
                    if not has_filestore:
                        logger.warning(f"⚠️ El backup {final_filename} no contiene filestore")
            
            # Obtener tamaño
            size_bytes = os.path.getsize(final_filepath)
            size_human = self._human_readable_size(size_bytes)
            
            logger.info(f"✅ Upload completado exitosamente")
            logger.info(f"📊 Tamaño final: {size_human} ({size_bytes} bytes)")
            logger.info(f"📁 Archivo: {final_filename}")
            
            return {
                'success': True,
                'message': f'Backup subido exitosamente{" (convertido de ZIP)" if is_zip else ""}',
                'filename': final_filename,
                'size_bytes': size_bytes,
                'size_human': size_human
            }
            
        except Exception as e:
            logger.error(f"❌ Error en upload: {str(e)}")
            logger.exception("Stack trace completo:")
            
            # Limpiar archivos si hubo error
            if 'final_filepath' in locals() and os.path.exists(final_filepath):
                logger.info(f"🧹 Eliminando archivo final: {final_filepath}")
                os.remove(final_filepath)
            if 'temp_path' in locals() and os.path.exists(temp_path):
                logger.info(f"🧹 Eliminando archivo temporal: {temp_path}")
                os.remove(temp_path)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _human_readable_size(size_bytes):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
