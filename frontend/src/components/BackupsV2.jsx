import { useState, useEffect } from 'react';
import axios from 'axios';
import { backupV2 } from '../lib/api';
import { Server, Settings, Download, Trash2, RefreshCw, AlertCircle, Clock, HardDrive, Play, Pause, Database, Upload, Pencil } from 'lucide-react';
import Toast from './Toast';

// Cliente axios local (api.js está gitignored, pero necesitamos enviar payloads nuevos)
const API_URL = import.meta.env.MODE === 'production'
  ? ''
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000');

const localApi = axios.create({
  timeout: 30000,
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

localApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default function BackupsV2() {
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterTerm, setFilterTerm] = useState('');
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [configModal, setConfigModal] = useState({ show: false, instance: null, config: null });
  const [backupListModal, setBackupListModal] = useState({ show: false, instance: null, backups: [] });
  const [restoreModal, setRestoreModal] = useState({ show: false, instance: null, backup: null });
  const [backupProgress, setBackupProgress] = useState({});
  const [restoreProgress, setRestoreProgress] = useState({});
  const [showUploadModal, setShowUploadModal] = useState({ show: false, instance: null });

  useEffect(() => {
    fetchInstances();
    
    // Verificar si hay una instancia en la URL
    const urlParams = new URLSearchParams(window.location.search);
    const instanceParam = urlParams.get('instance');
    if (instanceParam) {
      // Abrir modal de configuración para esta instancia
      setTimeout(() => handleConfigure(instanceParam), 500);
    }
    
    const interval = setInterval(fetchInstances, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchInstances = async () => {
    try {
      const response = await backupV2.listInstances();
      setInstances(response.data.instances || []);
    } catch (error) {
      console.error('Error fetching instances:', error);
      setToast({ show: true, message: 'Error al cargar instancias', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleConfigure = async (instanceName) => {
    try {
      const response = await backupV2.getInstanceConfig(instanceName);
      setConfigModal({ show: true, instance: instanceName, config: response.data.config });
    } catch (error) {
      setToast({ show: true, message: 'Error al cargar configuración', type: 'error' });
    }
  };

  const handleSaveConfig = async () => {
    try {
      await backupV2.updateInstanceConfig(configModal.instance, configModal.config);
      setToast({ show: true, message: 'Configuración actualizada', type: 'success' });
      setConfigModal({ show: false, instance: null, config: null });
      fetchInstances();
    } catch (error) {
      setToast({ show: true, message: 'Error al guardar configuración', type: 'error' });
    }
  };

  const handleToggleAutoBackup = async (instanceName, currentState) => {
    try {
      await backupV2.toggleAutoBackup(instanceName, !currentState);
      const newState = !currentState;
      setToast({ show: true, message: `Backup automático ${newState ? 'activado' : 'pausado'}`, type: 'success' });
      fetchInstances();
    } catch (error) {
      setToast({ show: true, message: 'Error al cambiar estado', type: 'error' });
    }
  };

  const handleManualBackup = async (instanceName) => {
    try {
      const customFilename = prompt('Nombre de archivo (opcional). Si lo dejás vacío usa el nombre automático:', '');
      if (customFilename === null) return;

      setBackupProgress({ ...backupProgress, [instanceName]: true });
      await localApi.post(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backup`, {
        custom_filename: customFilename || undefined,
      });
      setToast({ show: true, message: `Backup de ${instanceName} iniciado`, type: 'success' });
      setTimeout(() => {
        fetchInstances();
        setBackupProgress({ ...backupProgress, [instanceName]: false });
      }, 5000);
    } catch (error) {
      setBackupProgress({ ...backupProgress, [instanceName]: false });
      setToast({ show: true, message: 'Error al crear backup', type: 'error' });
    }
  };

  const handleRenameBackup = async (instanceName, oldFilename) => {
    try {
      const suggested = oldFilename.replace(/\.tar\.gz$/i, '');
      const newFilename = prompt(`Nuevo nombre para ${oldFilename}:`, suggested);
      if (newFilename === null) return;

      await localApi.post(
        `/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backups/${encodeURIComponent(oldFilename)}/rename`,
        { new_filename: newFilename }
      );

      setToast({ show: true, message: 'Backup renombrado', type: 'success' });
      handleViewBackups(instanceName);
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al renombrar backup', type: 'error' });
    }
  };

  const handleViewBackups = async (instanceName) => {
    try {
      const response = await backupV2.listBackups(instanceName);
      setBackupListModal({ show: true, instance: instanceName, backups: response.data.backups || [] });
    } catch (error) {
      setToast({ show: true, message: 'Error al cargar backups', type: 'error' });
    }
  };

  const handleDownloadBackup = async (instanceName, filename) => {
    try {
      const response = await backupV2.downloadBackup(instanceName, filename);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setToast({ show: true, message: 'Descarga iniciada', type: 'success' });
    } catch (error) {
      setToast({ show: true, message: 'Error al descargar backup', type: 'error' });
    }
  };

  const handleDeleteBackup = async (instanceName, filename) => {
    if (!confirm(`¿Eliminar el backup ${filename}?`)) return;
    try {
      await backupV2.deleteBackup(instanceName, filename);
      setToast({ show: true, message: 'Backup eliminado', type: 'success' });
      handleViewBackups(instanceName);
    } catch (error) {
      setToast({ show: true, message: 'Error al eliminar backup', type: 'error' });
    }
  };

  const handleRestoreBackup = (instanceName, backup) => {
    setRestoreModal({ show: true, instance: instanceName, backup: backup });
  };

  const handleConfirmRestore = async () => {
    const { instance, backup } = restoreModal;
    try {
      setRestoreProgress({ ...restoreProgress, [instance]: true });
      await backupV2.restoreBackup(instance, backup.filename);
      setToast({ show: true, message: `Restauración de ${instance} iniciada`, type: 'success' });
      setRestoreModal({ show: false, instance: null, backup: null });
      setBackupListModal({ show: false, instance: null, backups: [] });
      setTimeout(() => {
        fetchInstances();
        setRestoreProgress({ ...restoreProgress, [instance]: false });
      }, 10000);
    } catch (error) {
      setRestoreProgress({ ...restoreProgress, [instance]: false });
      setToast({ show: true, message: 'Error al restaurar backup', type: 'error' });
    }
  };

  const handleUploadBackup = async (file, onProgress) => {
    const { instance } = showUploadModal;
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      await backupV2.uploadBackup(instance, formData, onProgress);
      setToast({ show: true, message: 'Backup subido exitosamente', type: 'success' });
      setShowUploadModal({ show: false, instance: null });
      fetchInstances();
      // Actualizar la lista de backups si está abierta
      if (backupListModal.show && backupListModal.instance === instance) {
        handleViewBackups(instance);
      }
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al subir backup', type: 'error' });
    }
  };

  const filteredInstances = instances.filter(instance =>
    instance.name.toLowerCase().includes(filterTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Backups de Instancias</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-1">Gestión de backups por instancia de producción</p>
        </div>
        <button onClick={fetchInstances} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <input type="text" value={filterTerm} onChange={(e) => setFilterTerm(e.target.value)} placeholder="Buscar instancia..." className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
      </div>

      {filteredInstances.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
          <Database className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <p className="text-gray-600 dark:text-gray-300">{filterTerm ? 'No se encontraron instancias' : 'No hay instancias con backups configurados'}</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredInstances.map(instance => (
            <InstanceBackupCard key={instance.name} instance={instance} onConfigure={handleConfigure} onToggle={handleToggleAutoBackup} onBackup={handleManualBackup} onViewBackups={handleViewBackups} backupInProgress={backupProgress[instance.name]} restoreInProgress={restoreProgress[instance.name]} />
          ))}
        </div>
      )}

      {configModal.show && <ConfigModal instance={configModal.instance} config={configModal.config} onClose={() => setConfigModal({ show: false, instance: null, config: null })} onSave={handleSaveConfig} onChange={(field, value) => setConfigModal({ ...configModal, config: { ...configModal.config, [field]: value } })} />}
      {backupListModal.show && <BackupListModal instance={backupListModal.instance} backups={backupListModal.backups} onClose={() => setBackupListModal({ show: false, instance: null, backups: [] })} onDownload={handleDownloadBackup} onRestore={handleRestoreBackup} onDelete={handleDeleteBackup} onUpload={() => setShowUploadModal({ show: true, instance: backupListModal.instance })} onRename={handleRenameBackup} />}
      {restoreModal.show && <RestoreConfirmModal instance={restoreModal.instance} backup={restoreModal.backup} onClose={() => setRestoreModal({ show: false, instance: null, backup: null })} onConfirm={handleConfirmRestore} />}
      {showUploadModal.show && <UploadModal instance={showUploadModal.instance} onClose={() => setShowUploadModal({ show: false, instance: null })} onUpload={handleUploadBackup} />}
      {toast.show && <Toast message={toast.message} type={toast.type} onClose={() => setToast({ show: false, message: '', type: 'success' })} />}
    </div>
  );
}

function InstanceBackupCard({ instance, onConfigure, onToggle, onBackup, onViewBackups, backupInProgress, restoreInProgress }) {
  const statusColor = instance.auto_backup_enabled ? 'text-green-600' : 'text-gray-600';
  const statusBg = instance.auto_backup_enabled ? 'bg-green-100 dark:bg-green-900' : 'bg-gray-100 dark:bg-gray-700';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-lg ${statusBg}`}>
            <Server className={`w-6 h-6 ${statusColor}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{instance.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              {instance.auto_backup_enabled ? (
                <span className="flex items-center gap-1 text-sm text-green-600 dark:text-green-400">
                  <Play className="w-3 h-3" />
                  Activo
                </span>
              ) : (
                <span className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                  <Pause className="w-3 h-3" />
                  Pausado
                </span>
              )}
              {instance.auto_backup_enabled && <span className="text-sm text-gray-600 dark:text-gray-400">• {instance.schedule}</span>}
            </div>
          </div>
        </div>
        {restoreInProgress && (
          <div className="flex items-center gap-2 text-orange-600">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span className="text-sm">Restaurando...</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <Clock className="w-4 h-4" />
            Último backup
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            {instance.last_backup ? new Date(instance.last_backup).toLocaleString('es-AR') : 'Nunca'}
          </div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <Database className="w-4 h-4" />
            Backups
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">{instance.backup_count} archivos</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 text-sm mb-1">
            <HardDrive className="w-4 h-4" />
            Tamaño total
          </div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">{instance.total_size_human}</div>
        </div>
      </div>

      <div className="flex gap-2">
        <button onClick={() => onConfigure(instance.name)} className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          <Settings className="w-4 h-4" />
          Configurar
        </button>
        <button onClick={() => onToggle(instance.name, instance.auto_backup_enabled)} className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${instance.auto_backup_enabled ? 'text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20' : 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'}`}>
          {instance.auto_backup_enabled ? <><Pause className="w-4 h-4" />Pausar</> : <><Play className="w-4 h-4" />Activar</>}
        </button>
        <button onClick={() => onBackup(instance.name)} disabled={backupInProgress} className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          {backupInProgress ? <><RefreshCw className="w-4 h-4 animate-spin" />Creando...</> : <><Database className="w-4 h-4" />Backup Manual</>}
        </button>
        <button onClick={() => onViewBackups(instance.name)} className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
          <Download className="w-4 h-4" />
          Ver Backups ({instance.backup_count})
        </button>
      </div>
    </div>
  );
}

function ConfigModal({ instance, config, onClose, onSave, onChange }) {
  const schedulePresets = [
    { label: 'Diario 3:00 AM', value: '0 3 * * *' },
    { label: 'Diario 4:00 AM', value: '0 4 * * *' },
    { label: 'Semanal (Domingo 2:00 AM)', value: '0 2 * * 0' },
    { label: 'Mensual (Día 1, 2:00 AM)', value: '0 2 1 * *' },
  ];
  const retentionPresets = [7, 14, 30, 60, 90];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configurar Backups - {instance}</h3>
        
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={config.auto_backup_enabled} onChange={(e) => onChange('auto_backup_enabled', e.target.checked)} className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">Activar backups automáticos</span>
          </label>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Horario (Cron)</label>
          <select value={config.schedule} onChange={(e) => onChange('schedule', e.target.value)} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-2">
            {schedulePresets.map(preset => <option key={preset.value} value={preset.value}>{preset.label}</option>)}
            <option value="custom">Personalizado</option>
          </select>
          {!schedulePresets.find(p => p.value === config.schedule) && (
            <input type="text" value={config.schedule} onChange={(e) => onChange('schedule', e.target.value)} placeholder="0 3 * * *" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          )}
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Retención (días)</label>
          <div className="flex gap-2 mb-2">
            {retentionPresets.map(days => (
              <button key={days} onClick={() => onChange('retention_days', days)} className={`px-3 py-1 text-sm rounded-lg transition-colors ${config.retention_days === days ? 'bg-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'}`}>
                {days}d
              </button>
            ))}
          </div>
          <input type="number" value={config.retention_days} onChange={(e) => onChange('retention_days', parseInt(e.target.value))} min="1" max="365" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Prioridad</label>
          <select value={config.priority} onChange={(e) => onChange('priority', e.target.value)} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            <option value="high">Alta (crítico)</option>
            <option value="medium">Media (normal)</option>
            <option value="low">Baja (ocasional)</option>
            <option value="manual">Manual (sin automático)</option>
          </select>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">Cancelar</button>
          <button onClick={onSave} className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">Guardar</button>
        </div>
      </div>
    </div>
  );
}

function BackupListModal({ instance, backups, onClose, onDownload, onRestore, onDelete, onUpload, onRename }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Backups de {instance}</h3>
          <button onClick={onClose} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">✕</button>
        </div>

        {backups.length === 0 ? (
          <div className="text-center py-8">
            <Database className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 dark:text-gray-300">No hay backups disponibles</p>
          </div>
        ) : (
          <div className="space-y-2">
            {backups.map(backup => (
              <div key={backup.filename} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white">{backup.filename}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{backup.date} • {backup.size_human}</div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => onDownload(instance, backup.filename)} className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors" title="Descargar">
                    <Download className="w-4 h-4" />
                  </button>
                  <button onClick={() => onRename(instance, backup.filename)} className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors" title="Renombrar">
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button onClick={() => onRestore(instance, backup)} className="p-2 text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors" title="Restaurar">
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button onClick={() => onDelete(instance, backup.filename)} className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors" title="Eliminar">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 flex gap-3">
          <button onClick={onUpload} className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2">
            <Upload className="w-4 h-4" />
            Subir Backup
          </button>
          <button onClick={onClose} className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">Cerrar</button>
        </div>
      </div>
    </div>
  );
}

function RestoreConfirmModal({ instance, backup, onClose, onConfirm }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-orange-100 dark:bg-orange-900 p-3 rounded-full">
            <AlertCircle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Confirmar Restauración</h3>
        </div>

        <div className="mb-4 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
          <p className="text-sm text-orange-800 dark:text-orange-200 font-semibold mb-2">⚠️ ADVERTENCIA: Esta acción sobrescribirá los datos actuales</p>
          <p className="text-sm text-orange-700 dark:text-orange-300">Estás a punto de restaurar la instancia <strong>{instance}</strong> con el backup:</p>
          <div className="mt-2 p-2 bg-white dark:bg-gray-700 rounded">
            <div className="text-sm font-mono text-gray-900 dark:text-white">{backup.filename}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">{backup.date} • {backup.size_human}</div>
          </div>
          <p className="text-sm text-orange-700 dark:text-orange-300 mt-2">Esto reemplazará:</p>
          <ul className="text-sm text-orange-700 dark:text-orange-300 list-disc list-inside mt-1">
            <li>La base de datos completa</li>
            <li>Todos los archivos del filestore</li>
          </ul>
          <p className="text-sm text-orange-700 dark:text-orange-300 mt-2">El servicio se reiniciará automáticamente.</p>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">Cancelar</button>
          <button onClick={onConfirm} className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors">Confirmar Restauración</button>
        </div>
      </div>
    </div>
  );
}

// Modal de upload
function UploadModal({ instance, onClose, onUpload }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({
    percentage: 0,
    loaded: 0,
    total: 0,
    speed: 0,
    eta: 0,
    status: 'idle'
  });
  const [startTime, setStartTime] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.tar.gz') || file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        alert('Por favor selecciona un archivo .tar.gz o .zip');
      }
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.tar.gz') && !file.name.endsWith('.zip')) {
        alert('Por favor selecciona un archivo .tar.gz o .zip válido');
        e.target.value = '';
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      const uploadStartTime = Date.now();
      setStartTime(uploadStartTime);
      setUploadProgress({ 
        percentage: 0,
        loaded: 0,
        total: 0,
        speed: 0,
        eta: 0,
        status: 'uploading' 
      });
      
      const onProgress = (progressEvent) => {
        const { loaded, total } = progressEvent;
        const percentage = Math.round((loaded * 100) / total);
        
        const currentTime = Date.now();
        const elapsedTime = (currentTime - uploadStartTime) / 1000;
        const speed = elapsedTime > 0 ? loaded / elapsedTime : 0;
        
        const remainingBytes = total - loaded;
        const eta = speed > 0 ? remainingBytes / speed : 0;
        
        setUploadProgress({
          percentage,
          loaded,
          total,
          speed,
          eta,
          status: percentage === 100 ? 'validating' : 'uploading'
        });
      };
      
      onUpload(selectedFile, onProgress);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatSpeed = (bytesPerSecond) => {
    if (bytesPerSecond === 0) return '0 KB/s';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    const i = Math.floor(Math.log(bytesPerSecond) / Math.log(k));
    return Math.round(bytesPerSecond / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatTime = (seconds) => {
    if (seconds === 0 || !isFinite(seconds)) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const getStatusText = () => {
    switch (uploadProgress.status) {
      case 'uploading':
        return '📤 Subiendo archivo...';
      case 'validating':
        return '🔍 Validando estructura...';
      case 'complete':
        return '✅ Completado';
      case 'error':
        return '❌ Error';
      default:
        return 'Listo para subir';
    }
  };

  const isUploading = uploadProgress.status === 'uploading' || uploadProgress.status === 'validating';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <Upload className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Subir Backup - {instance}
            </h3>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
            <p className="text-sm text-blue-800 dark:text-blue-200 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                Sube backups en formato <strong>.tar.gz o .zip</strong> compatibles con Odoo Online.
                El archivo debe contener <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">dump.sql</code> y <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">filestore/</code>
              </span>
            </p>
          </div>

          {!isUploading ? (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragActive
                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
            >
              {selectedFile ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-center">
                    <Database className="w-12 h-12 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{selectedFile.name}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
                  </div>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-sm text-red-600 hover:text-red-700 dark:text-red-400"
                  >
                    Cambiar archivo
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-center">
                    <Upload className="w-12 h-12 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-gray-700 dark:text-gray-300 font-medium">
                      Arrastra un archivo aquí
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">o</p>
                  </div>
                  <label className="inline-block">
                    <input
                      type="file"
                      accept=".tar.gz,.zip"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <span className="cursor-pointer bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors inline-block">
                      Seleccionar archivo
                    </span>
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Archivos .tar.gz o .zip
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {getStatusText()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedFile?.name}
                </p>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>{uploadProgress.percentage}%</span>
                  <span>{formatFileSize(uploadProgress.loaded)} / {formatFileSize(uploadProgress.total)}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-purple-600 h-full transition-all duration-300 ease-out"
                    style={{ width: `${uploadProgress.percentage}%` }}
                  ></div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div className="text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Velocidad</p>
                  <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">
                    {formatSpeed(uploadProgress.speed)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Tiempo restante</p>
                  <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">
                    {formatTime(uploadProgress.eta)}
                  </p>
                </div>
              </div>

              {uploadProgress.status === 'validating' && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                  <p className="text-sm text-blue-800 dark:text-blue-200 flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Validando estructura del backup...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-3 p-6 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <button
            onClick={onClose}
            disabled={isUploading}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors disabled:opacity-50"
          >
            {isUploading ? 'Subiendo...' : 'Cancelar'}
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                {uploadProgress.percentage}%
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Subir Backup
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
