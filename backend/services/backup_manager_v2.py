import os
import json
import subprocess
from datetime import datetime
import glob
import logging
import re

from config import Config

# Configurar logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BackupManagerV2:
    """
    Sistema de backups multi-instancia
    Permite gestionar backups individuales por cada instancia de producción
    """
    
    def __init__(self, backup_dir=None, scripts_path=None):
        self.backup_dir = backup_dir or Config.BACKUPS_PATH
        self.scripts_path = scripts_path or Config.SCRIPTS_PATH
        self.instances_dir = os.path.join(self.backup_dir, 'instances')
        self.global_config_file = os.path.join(self.backup_dir, 'backup_config.json')
        self._ensure_directories()
        self._load_global_config()
    
    def _ensure_directories(self):
        """Asegura que los directorios necesarios existen"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.instances_dir, exist_ok=True)
    
    def _load_global_config(self):
        """Carga la configuración global de backups"""
        if os.path.exists(self.global_config_file):
            with open(self.global_config_file, 'r') as f:
                self.global_config = json.load(f)
        else:
            # Configuración por defecto
            self.global_config = {
                'global_retention_days': 7,
                'max_backups_per_instance': 30,
                'max_total_size_gb': 100,
                'instances': {}
            }
            self._save_global_config()
    
    def _save_global_config(self):
        """Guarda la configuración global"""
        with open(self.global_config_file, 'w') as f:
            json.dump(self.global_config, f, indent=2)
    
    def _get_instance_dir(self, instance_name):
        """Obtiene el directorio de una instancia"""
        return os.path.join(self.instances_dir, instance_name)
    
    def _get_instance_config_file(self, instance_name):
        """Obtiene el archivo de configuración de una instancia"""
        return os.path.join(self._get_instance_dir(instance_name), 'config.json')

    def _is_safe_backup_filename(self, filename):
        """Valida que el filename sea seguro y esperado (sin rutas, solo .tar.gz)."""
        if not filename or not isinstance(filename, str):
            return False

        # Evitar path traversal / paths absolutos
        if os.path.basename(filename) != filename:
            return False

        if filename.startswith('.'):
            return False

        if not filename.endswith('.tar.gz'):
            return False

        # Permitimos letras/números/puntos/guiones/underscores. (tar.gz incluye puntos)
        return re.fullmatch(r"[A-Za-z0-9._-]+\.tar\.gz", filename) is not None

    def _normalize_backup_filename(self, filename):
        """Normaliza un nombre ingresado por usuario a un filename seguro *.tar.gz."""
        if not filename or not isinstance(filename, str):
            return None

        name = filename.strip()
        if not name:
            return None

        # Reemplazar caracteres no permitidos por '_'
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
        if not name:
            return None

        if not name.endswith('.tar.gz'):
            name = f"{name}.tar.gz"

        return name if self._is_safe_backup_filename(name) else None
    
    def _load_instance_config(self, instance_name):
        """Carga la configuración de una instancia"""
        config_file = self._get_instance_config_file(instance_name)
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Configuración por defecto para nueva instancia
            default_config = {
                'instance_name': instance_name,
                'auto_backup_enabled': False,  # Deshabilitado por defecto
                'schedule': '0 3 * * *',  # 3 AM diario
                'retention_days': 7,
                'priority': 'medium',
                'last_backup': None,
                'last_backup_status': None,
                'last_backup_size': 0,
                'backup_count': 0,
                'total_size': 0,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Crear directorio y guardar config
            os.makedirs(self._get_instance_dir(instance_name), exist_ok=True)
            self._save_instance_config(instance_name, default_config)
            
            return default_config
    
    def _save_instance_config(self, instance_name, config):
        """Guarda la configuración de una instancia"""
        config['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        config_file = self._get_instance_config_file(instance_name)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _get_all_production_instances(self):
        """Obtiene todas las instancias de producción del sistema usando el mismo método que instance_manager"""
        prod_instances = []
        
        # Importar instance_manager para usar su método de listado
        try:
            from services.instance_manager import InstanceManager
            manager = InstanceManager()
            instances = manager.list_production_instances()
            
            # Extraer solo los nombres de las instancias
            prod_instances = [inst['name'] for inst in instances]
            logger.info(f"Found {len(prod_instances)} production instances: {prod_instances}")
        except Exception as e:
            logger.error(f"Error getting production instances: {e}")
            # Fallback: buscar en rutas conocidas
            prod_root = Config.PROD_ROOT if hasattr(Config, 'PROD_ROOT') else '/home/mtg/apps/production'
            if os.path.exists(prod_root):
                for item in os.listdir(prod_root):
                    item_path = os.path.join(prod_root, item)
                    if os.path.isdir(item_path):
                        # Verificar si tiene odoo.conf (indicador de instancia válida)
                        if os.path.exists(os.path.join(item_path, 'odoo.conf')):
                            prod_instances.append(item)
        
        return prod_instances
    
    def list_instances_with_backups(self):
        """Lista todas las instancias de producción con su configuración de backup"""
        instances = []
        
        # Obtener todas las instancias de producción del sistema
        all_prod_instances = self._get_all_production_instances()
        
        # Crear un set con las instancias que ya tienen configuración
        configured_instances = set()
        if os.path.exists(self.instances_dir):
            configured_instances = set(os.listdir(self.instances_dir))
        
        # Procesar todas las instancias de producción
        for instance_name in all_prod_instances:
            # Cargar o crear configuración (esto crea la carpeta si no existe)
            config = self._load_instance_config(instance_name)
            instance_dir = self._get_instance_dir(instance_name)
            
            # Contar backups
            pattern = os.path.join(instance_dir, '*.tar.gz')
            backup_files = glob.glob(pattern)
            backup_count = len(backup_files)
            
            # Calcular tamaño total
            total_size = sum(os.path.getsize(f) for f in backup_files if os.path.exists(f))
            
            instances.append({
                'name': instance_name,
                'auto_backup_enabled': config.get('auto_backup_enabled', False),
                'schedule': config.get('schedule', '0 3 * * *'),
                'retention_days': config.get('retention_days', 7),
                'priority': config.get('priority', 'medium'),
                'last_backup': config.get('last_backup'),
                'last_backup_status': config.get('last_backup_status'),
                'backup_count': backup_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_human': self._human_readable_size(total_size),
                'is_new': instance_name not in configured_instances  # Indicar si es nueva
            })
        
        # Ordenar por nombre
        instances.sort(key=lambda x: x['name'])
        
        return {
            'instances': instances,
            'total_count': len(instances)
        }
    
    def get_instance_config(self, instance_name):
        """Obtiene la configuración de una instancia"""
        config = self._load_instance_config(instance_name)
        
        # Agregar estadísticas actuales
        pattern = os.path.join(self._get_instance_dir(instance_name), '*.tar.gz')
        backup_files = glob.glob(pattern)
        backup_count = len(backup_files)
        total_size = sum(os.path.getsize(f) for f in backup_files if os.path.exists(f))
        
        config['backup_count'] = backup_count
        config['total_size'] = total_size
        config['total_size_mb'] = round(total_size / (1024 * 1024), 2)
        config['total_size_human'] = self._human_readable_size(total_size)
        
        return {'success': True, 'config': config}
    
    def update_instance_config(self, instance_name, **kwargs):
        """Actualiza la configuración de una instancia"""
        config = self._load_instance_config(instance_name)
        
        # Actualizar campos permitidos
        allowed_fields = ['auto_backup_enabled', 'schedule', 'retention_days', 'priority']
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                config[field] = kwargs[field]
        
        self._save_instance_config(instance_name, config)
        
        # Actualizar crontab si cambió el schedule o el estado
        if 'schedule' in kwargs or 'auto_backup_enabled' in kwargs:
            self._update_crontab()
        
        return {'success': True, 'config': config}
    
    def toggle_auto_backup(self, instance_name, enabled):
        """Activa o pausa el backup automático de una instancia"""
        return self.update_instance_config(
            instance_name,
            auto_backup_enabled=bool(enabled)
        )
    
    def create_backup(self, instance_name, custom_filename=None):
        """Crea un backup manual de una instancia"""
        script_path = os.path.join(self.scripts_path, 'odoo/backup-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de backup no encontrado'}
        
        # Asegurar que existe el directorio de la instancia
        instance_dir = self._get_instance_dir(instance_name)
        os.makedirs(instance_dir, exist_ok=True)
        
        # Cargar o crear configuración
        config = self._load_instance_config(instance_name)
        
        try:
            safe_custom = self._normalize_backup_filename(custom_filename) if custom_filename else None

            # Ejecutar script en background
            log_file = f'/tmp/odoo-backup-{instance_name}-latest.log'
            if safe_custom:
                cmd = f"/bin/bash {script_path} {instance_name} {safe_custom} > {log_file} 2>&1 &"
            else:
                cmd = f"/bin/bash {script_path} {instance_name} > {log_file} 2>&1 &"
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
                'message': f'Backup de {instance_name} iniciado',
                'log_file': log_file
            }
        except Exception as e:
            logger.error(f"Error creating backup for {instance_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_backups(self, instance_name):
        """Lista todos los backups de una instancia"""
        instance_dir = self._get_instance_dir(instance_name)
        pattern = os.path.join(instance_dir, '*.tar.gz')
        backups = []

        backup_files = glob.glob(pattern)
        backup_files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)

        for backup_file in backup_files:
            try:
                basename = os.path.basename(backup_file)

                # Extraer timestamp si aplica al formato default: backup_YYYYMMDD_HHMMSS.tar.gz
                timestamp = 'unknown'
                parts = basename.replace('.tar.gz', '').split('_')
                if len(parts) >= 3 and parts[0] == 'backup' and parts[1].isdigit() and parts[2].isdigit():
                    date_str = parts[1]
                    time_str = parts[2]
                    timestamp = f"{date_str}_{time_str}"
                
                # Información del archivo
                stat = os.stat(backup_file)
                size_bytes = stat.st_size
                
                backups.append({
                    'filename': basename,
                    'path': backup_file,
                    'timestamp': timestamp,
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'size_bytes': size_bytes,
                    'size_mb': round(size_bytes / (1024 * 1024), 2),
                    'size_human': self._human_readable_size(size_bytes)
                })
            except Exception as e:
                logger.error(f"Error reading backup {backup_file}: {e}")
                continue
        
        # Calcular estadísticas
        total_size = sum(b['size_bytes'] for b in backups)
        config = self._load_instance_config(instance_name)
        
        return {
            'instance_name': instance_name,
            'backups': backups,
            'count': len(backups),
            'total_size_bytes': total_size,
            'total_size_human': self._human_readable_size(total_size),
            'retention_days': config.get('retention_days', 7)
        }
    
    def delete_backup(self, instance_name, filename):
        """Elimina un backup específico de una instancia"""
        instance_dir = self._get_instance_dir(instance_name)
        backup_path = os.path.join(instance_dir, filename)
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup no encontrado'}
        
        if not self._is_safe_backup_filename(filename):
            return {'success': False, 'error': 'Nombre de archivo inválido'}
        
        try:
            os.remove(backup_path)
            return {'success': True, 'message': f'Backup {filename} eliminado'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_backup_log(self, instance_name):
        """Obtiene el log del último backup de una instancia"""
        log_file = f'/tmp/odoo-backup-{instance_name}-latest.log'
        
        if not os.path.exists(log_file):
            return {'log': 'No hay log disponible', 'exists': False}
        
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            return {'log': log_content, 'exists': True}
        except Exception as e:
            return {'log': f'Error al leer log: {str(e)}', 'exists': False}
    
    def restore_backup(self, instance_name, filename):
        """Restaura un backup de una instancia"""
        instance_dir = self._get_instance_dir(instance_name)
        backup_path = os.path.join(instance_dir, filename)
        
        if not os.path.exists(backup_path):
            return {'success': False, 'error': 'Backup no encontrado'}
        
        if not self._is_safe_backup_filename(filename):
            return {'success': False, 'error': 'Nombre de archivo inválido'}
        
        script_path = os.path.join(self.scripts_path, 'odoo/restore-instance.sh')
        
        if not os.path.exists(script_path):
            return {'success': False, 'error': 'Script de restauración no encontrado'}
        
        try:
            # Ejecutar script de restauración en background
            log_file = f'/tmp/odoo-restore-{instance_name}-latest.log'
            cmd = f"/bin/bash {script_path} {instance_name} {backup_path} > {log_file} 2>&1 &"
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
                'message': f'Restauración de {instance_name} iniciada',
                'log_file': log_file,
                'backup_file': filename
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def rename_backup(self, instance_name, old_filename, new_filename):
        """Renombra un backup dentro del directorio de la instancia"""
        if not self._is_safe_backup_filename(old_filename):
            return {'success': False, 'error': 'Nombre original inválido'}

        normalized_new = self._normalize_backup_filename(new_filename)
        if not normalized_new:
            return {'success': False, 'error': 'Nuevo nombre inválido'}

        instance_dir = self._get_instance_dir(instance_name)
        old_path = os.path.join(instance_dir, old_filename)
        new_path = os.path.join(instance_dir, normalized_new)

        if not os.path.exists(old_path):
            return {'success': False, 'error': 'Backup no encontrado'}

        if os.path.exists(new_path):
            return {'success': False, 'error': 'Ya existe un backup con ese nombre'}

        try:
            os.rename(old_path, new_path)
            return {
                'success': True,
                'message': 'Backup renombrado',
                'old_filename': old_filename,
                'new_filename': normalized_new
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_restore_log(self, instance_name):
        """Obtiene el log de la última restauración de una instancia"""
        log_file = f'/tmp/odoo-restore-{instance_name}-latest.log'
        
        if not os.path.exists(log_file):
            return {'log': 'No hay log de restauración disponible', 'exists': False}
        
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            return {'log': log_content, 'exists': True}
        except Exception as e:
            return {'log': f'Error al leer log: {str(e)}', 'exists': False}
    
    def get_global_stats(self):
        """Obtiene estadísticas globales de todos los backups"""
        instances_data = self.list_instances_with_backups()
        instances = instances_data['instances']
        
        total_backups = sum(i['backup_count'] for i in instances)
        total_size = sum(i['total_size_bytes'] for i in instances)
        enabled_count = sum(1 for i in instances if i['auto_backup_enabled'])
        
        return {
            'total_instances': len(instances),
            'enabled_instances': enabled_count,
            'disabled_instances': len(instances) - enabled_count,
            'total_backups': total_backups,
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 2),
            'total_size_human': self._human_readable_size(total_size),
            'instances': instances
        }
    
    def _update_crontab(self):
        """Actualiza el crontab con todas las instancias habilitadas"""
        cron_comment = "# Odoo Backups - Managed by API-DEV"
        script_path = os.path.join(self.scripts_path, 'odoo/backup-instance.sh')
        cron_log = os.path.join(self.backup_dir, 'cron.log')
        
        # Leer crontab actual
        try:
            result = subprocess.run(['/usr/bin/crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
        except Exception as e:
            logger.error(f"Error reading crontab: {e}")
            current_cron = ""
        
        # Eliminar líneas antiguas de backups
        lines = []
        skip_next = False
        for line in current_cron.split('\n'):
            if cron_comment in line:
                skip_next = True
                continue
            if skip_next and script_path in line:
                skip_next = False
                continue
            if line.strip():
                lines.append(line)
        
        # Agregar nuevas líneas para instancias habilitadas
        instances_data = self.list_instances_with_backups()
        enabled_instances = [i for i in instances_data['instances'] if i['auto_backup_enabled']]
        
        if enabled_instances:
            lines.append(cron_comment)
            for instance in enabled_instances:
                schedule = instance['schedule']
                instance_name = instance['name']
                lines.append(f"{schedule} {script_path} {instance_name} >> {cron_log} 2>&1")
        
        # Escribir nuevo crontab
        new_cron = '\n'.join(lines) + '\n'
        try:
            process = subprocess.Popen(['/usr/bin/crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
            logger.info(f"Crontab updated with {len(enabled_instances)} enabled instances")
        except Exception as e:
            raise Exception(f"Error updating crontab: {e}")
    
    def _human_readable_size(self, size_bytes):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def upload_backup(self, instance_name, file):
        """Sube un archivo de backup para una instancia específica"""
        import tarfile
        import zipfile
        import tempfile
        import shutil
        import sys
        
        try:
            logger.info("=" * 80)
            logger.info(f"🚀 BACKUP_MANAGER_V2: Iniciando upload para instancia: {instance_name}")
            logger.info(f"🚀 Archivo: {file.filename}")
            sys.stdout.flush()
            
            # Verificar que la instancia existe
            instance_dir = os.path.join(self.instances_dir, instance_name)
            if not os.path.exists(instance_dir):
                return {'success': False, 'error': f'Instancia {instance_name} no encontrada'}
            
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
                    final_filename = f"backup_{timestamp}.tar.gz"
                    final_filepath = os.path.join(instance_dir, final_filename)
                    
                    with tarfile.open(final_filepath, 'w:gz') as tar:
                        for item in os.listdir(extract_dir):
                            logger.info(f"➕ Agregando: {item}")
                            tar.add(os.path.join(extract_dir, item), arcname=item)
                    
                    logger.info(f"✅ TAR.GZ creado: {final_filepath}")
                    
                    # Limpiar temporales
                    logger.info("🧹 Limpiando archivos temporales...")
                    shutil.rmtree(extract_dir)
                    os.remove(temp_path)
                    
                except Exception as e:
                    logger.error(f"❌ Error en conversión ZIP: {str(e)}")
                    if os.path.exists(extract_dir):
                        shutil.rmtree(extract_dir)
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return {'success': False, 'error': f'Error al procesar ZIP: {str(e)}'}
            
            else:
                # Es TAR.GZ, validar estructura
                logger.info("🔍 Validando estructura del TAR.GZ...")
                try:
                    with tarfile.open(temp_path, 'r:gz') as tar:
                        members = tar.getnames()
                        has_dump = any('dump.sql' in m for m in members)
                        has_filestore = any('filestore' in m for m in members)
                        
                        if not has_dump:
                            logger.error("❌ El backup no contiene dump.sql")
                            os.remove(temp_path)
                            return {'success': False, 'error': 'El backup no contiene dump.sql'}
                        
                        if not has_filestore:
                            logger.warning("⚠️ El backup no contiene filestore")
                        
                        logger.info("✅ Estructura válida")
                    
                    # Mover a directorio final
                    final_filename = f"backup_{timestamp}.tar.gz"
                    final_filepath = os.path.join(instance_dir, final_filename)
                    shutil.move(temp_path, final_filepath)
                    logger.info(f"✅ Archivo movido a: {final_filepath}")
                    
                except Exception as e:
                    logger.error(f"❌ Error validando TAR.GZ: {str(e)}")
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return {'success': False, 'error': f'Error al validar TAR.GZ: {str(e)}'}
            
            # Actualizar configuración de la instancia
            final_size = os.path.getsize(final_filepath)
            config = self.get_instance_config(instance_name)
            config['last_backup'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            config['last_backup_status'] = 'uploaded'
            config['last_backup_size'] = final_size
            config['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._save_instance_config(instance_name, config)
            
            logger.info("=" * 80)
            logger.info(f"✅ Upload completado exitosamente")
            logger.info(f"📁 Archivo final: {final_filename}")
            logger.info(f"📊 Tamaño: {final_size / 1024 / 1024:.2f}MB")
            logger.info("=" * 80)
            sys.stdout.flush()
            
            return {
                'success': True,
                'filename': final_filename,
                'size': final_size,
                'size_human': self._human_readable_size(final_size),
                'message': 'Backup subido exitosamente'
            }
            
        except Exception as e:
            logger.error(f"💥 Error en upload_backup: {str(e)}")
            logger.exception("Stack trace:")
            sys.stdout.flush()
            return {'success': False, 'error': str(e)}
