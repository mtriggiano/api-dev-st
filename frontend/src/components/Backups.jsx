import { useState, useEffect } from 'react';
import { backup } from '../lib/api';
import { Database, Download, Trash2, RefreshCw, Settings, HardDrive, Calendar, Clock, AlertCircle, RotateCcw, AlertTriangle, CheckCircle2, XCircle, Upload } from 'lucide-react';
import Toast from './Toast';

export default function Backups() {
  const [backupList, setBackupList] = useState([]);
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState({});
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showLogModal, setShowLogModal] = useState(false);
  const [backupLog, setBackupLog] = useState('');
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [restoreBackup, setRestoreBackup] = useState(null);
  const [restoreLog, setRestoreLog] = useState('');
  const [showRestoreLogModal, setShowRestoreLogModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [stats, setStats] = useState({ count: 0, total_size_human: '0 B' });

  useEffect(() => {
    fetchBackups();
    fetchConfig();
    const interval = setInterval(fetchBackups, 30000); // Actualizar cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  const fetchBackups = async () => {
    try {
      const response = await backup.list();
      setBackupList(response.data.backups || []);
      setStats({
        count: response.data.count || 0,
        total_size_human: response.data.total_size_human || '0 B'
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching backups:', error);
      setLoading(false);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await backup.getConfig();
      setConfig(response.data);
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const handleCreateBackup = async () => {
    setActionLoading({ create: true });
    try {
      const response = await backup.create();
      setToast({ show: true, message: 'Backup iniciado. Esto puede tardar varios minutos.', type: 'success' });
      
      // Mostrar log
      setShowLogModal(true);
      setBackupLog('Iniciando backup...\n');
      
      // Polling del log cada 3 segundos
      const logInterval = setInterval(async () => {
        try {
          const logResponse = await backup.getLog();
          setBackupLog(logResponse.data.log || 'Esperando...');
          
          // Si el log contiene "✅ Backup completado" significa que terminó
          if (logResponse.data.log && logResponse.data.log.includes('✅ Backup completado')) {
            clearInterval(logInterval);
            fetchBackups();
            setTimeout(() => {
              setShowLogModal(false);
              setToast({ show: true, message: 'Backup completado exitosamente', type: 'success' });
            }, 3000);
          }
        } catch (err) {
          console.error('Error fetching log:', err);
        }
      }, 3000);
      
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al crear backup', type: 'error' });
    } finally {
      setActionLoading({ create: false });
    }
  };

  const handleDownloadBackup = async (filename) => {
    setActionLoading({ [`download-${filename}`]: true });
    try {
      const response = await backup.download(filename);
      
      // Crear URL del blob y descargar
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      setToast({ show: true, message: 'Descarga iniciada', type: 'success' });
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al descargar backup', type: 'error' });
    } finally {
      setActionLoading({ [`download-${filename}`]: false });
    }
  };

  const handleDeleteBackup = async (filename) => {
    if (!confirm(`¿Estás seguro de eliminar el backup ${filename}?`)) return;
    
    setActionLoading({ [`delete-${filename}`]: true });
    try {
      await backup.delete(filename);
      setToast({ show: true, message: 'Backup eliminado', type: 'success' });
      fetchBackups();
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al eliminar backup', type: 'error' });
    } finally {
      setActionLoading({ [`delete-${filename}`]: false });
    }
  };

  const handleRestoreClick = (bk) => {
    setRestoreBackup(bk);
    setShowRestoreModal(true);
  };

  const handleRestoreConfirm = async () => {
    setShowRestoreModal(false);
    setActionLoading({ [`restore-${restoreBackup.filename}`]: true });
    
    try {
      const response = await backup.restore(restoreBackup.filename);
      setToast({ show: true, message: 'Restauración iniciada. El sistema estará inactivo por unos minutos.', type: 'success' });
      
      // Mostrar log de restauración
      setShowRestoreLogModal(true);
      setRestoreLog('Iniciando restauración...\n');
      
      // Polling del log cada 5 segundos
      const logInterval = setInterval(async () => {
        try {
          const logResponse = await backup.getRestoreLog();
          setRestoreLog(logResponse.data.log || 'Esperando...');
          
          // Si el log contiene "RESTAURACIÓN COMPLETADA" significa que terminó
          if (logResponse.data.log && logResponse.data.log.includes('RESTAURACIÓN COMPLETADA')) {
            clearInterval(logInterval);
            fetchBackups();
            setTimeout(() => {
              setShowRestoreLogModal(false);
              setToast({ show: true, message: 'Restauración completada exitosamente', type: 'success' });
            }, 5000);
          }
          
          // Si hay error
          if (logResponse.data.log && logResponse.data.log.includes('ERROR EN LA RESTAURACIÓN')) {
            clearInterval(logInterval);
            setTimeout(() => {
              setShowRestoreLogModal(false);
              setToast({ show: true, message: 'Error en la restauración. Sistema restaurado al estado anterior.', type: 'error' });
            }, 5000);
          }
        } catch (err) {
          console.error('Error fetching restore log:', err);
        }
      }, 5000);
      
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al iniciar restauración', type: 'error' });
    } finally {
      setActionLoading({ [`restore-${restoreBackup.filename}`]: false });
    }
  };

  const handleUpdateConfig = async (newConfig) => {
    try {
      await backup.updateConfig(newConfig);
      setConfig({ ...config, ...newConfig });
      setShowConfigModal(false);
      setToast({ show: true, message: 'Configuración actualizada', type: 'success' });
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al actualizar configuración', type: 'error' });
    }
  };

  const handleUploadBackup = async (file, onProgress) => {
    setActionLoading({ upload: true });
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await backup.upload(formData, onProgress);
      setToast({ show: true, message: 'Backup subido exitosamente', type: 'success' });
      setShowUploadModal(false);
      fetchBackups();
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al subir backup', type: 'error' });
    } finally {
      setActionLoading({ upload: false });
    }
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('es-AR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Backups de Producción</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Gestión de copias de seguridad completas (BD + Filestore)
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowConfigModal(true)}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Settings className="w-5 h-5" />
            Configuración
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Upload className="w-5 h-5" />
            Subir Backup
          </button>
          <button
            onClick={handleCreateBackup}
            disabled={actionLoading.create}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Database className="w-5 h-5" />
            {actionLoading.create ? 'Creando...' : 'Crear Backup'}
          </button>
        </div>
      </div>

      {/* Tarjetas de estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total de Backups</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.count}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <HardDrive className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Espacio Utilizado</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_size_human}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <Calendar className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Retención</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{config.retention_days || 7} días</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de backups */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Backups Disponibles</h3>
        </div>
        
        {backupList.length === 0 ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No hay backups disponibles</p>
            <p className="text-sm mt-1">Crea tu primer backup haciendo clic en el botón de arriba</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {backupList.map((bk) => (
              <div key={bk.filename} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <Database className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{bk.filename}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatDate(bk.date)}
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="w-4 h-4" />
                            {bk.size_human}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRestoreClick(bk)}
                      disabled={actionLoading[`restore-${bk.filename}`]}
                      className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-colors disabled:opacity-50"
                      title="Restaurar backup"
                    >
                      <RotateCcw className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDownloadBackup(bk.filename)}
                      disabled={actionLoading[`download-${bk.filename}`]}
                      className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors disabled:opacity-50"
                      title="Descargar backup"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteBackup(bk.filename)}
                      disabled={actionLoading[`delete-${bk.filename}`]}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-50"
                      title="Eliminar backup"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal de configuración */}
      {showConfigModal && (
        <ConfigModal
          config={config}
          onClose={() => setShowConfigModal(false)}
          onSave={handleUpdateConfig}
        />
      )}

      {/* Modal de log */}
      {showLogModal && (
        <LogModal
          log={backupLog}
          onClose={() => setShowLogModal(false)}
          title="Log de Backup"
        />
      )}

      {/* Modal de restauración */}
      {showRestoreModal && restoreBackup && (
        <RestoreModal
          backup={restoreBackup}
          onClose={() => setShowRestoreModal(false)}
          onConfirm={handleRestoreConfirm}
        />
      )}

      {/* Modal de log de restauración */}
      {showRestoreLogModal && (
        <LogModal
          log={restoreLog}
          onClose={() => setShowRestoreLogModal(false)}
          title="Log de Restauración"
        />
      )}

      {/* Modal de upload */}
      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onUpload={handleUploadBackup}
          loading={actionLoading.upload}
        />
      )}

      {/* Toast de notificaciones */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast({ show: false, message: '', type: 'success' })}
        />
      )}
    </div>
  );
}

// Modal de configuración
function ConfigModal({ config, onClose, onSave }) {
  const [retentionDays, setRetentionDays] = useState(config.retention_days || 7);
  const [autoBackupEnabled, setAutoBackupEnabled] = useState(config.auto_backup_enabled !== false);

  const handleSave = () => {
    onSave({
      retention_days: parseInt(retentionDays),
      auto_backup_enabled: autoBackupEnabled
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Configuración de Backups</h3>
        </div>

        <div className="p-6 space-y-4">
          {/* Retención */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Días de retención
            </label>
            <input
              type="number"
              min="1"
              max="90"
              value={retentionDays}
              onChange={(e) => setRetentionDays(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Los backups más antiguos se eliminarán automáticamente
            </p>
          </div>

          {/* Backup automático */}
          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={autoBackupEnabled}
                onChange={(e) => setAutoBackupEnabled(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Backup automático
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Ejecutar backup diariamente a las 3:00 AM
                </p>
              </div>
            </label>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3">
            <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>Los backups NO están neutralizados. Son copias exactas de producción para restauración ante desastres.</span>
            </p>
          </div>
        </div>

        <div className="flex gap-3 p-6 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal de upload
function UploadModal({ onClose, onUpload, loading }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({
    percentage: 0,
    loaded: 0,
    total: 0,
    speed: 0,
    eta: 0,
    status: 'idle' // idle, uploading, validating, complete, error
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
        
        // Calcular velocidad (bytes por segundo)
        const currentTime = Date.now();
        const elapsedTime = (currentTime - uploadStartTime) / 1000; // segundos
        const speed = elapsedTime > 0 ? loaded / elapsedTime : 0; // bytes/segundo
        
        // Calcular tiempo estimado restante
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
              Subir Backup
            </h3>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Información */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
            <p className="text-sm text-blue-800 dark:text-blue-200 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                Sube backups en formato <strong>.tar.gz o .zip</strong> compatibles con Odoo Online.
                El archivo debe contener <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">dump.sql</code> y <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">filestore/</code>
              </span>
            </p>
          </div>

          {/* Área de drag & drop o progreso */}
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
              {/* Estado */}
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {getStatusText()}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {selectedFile?.name}
                </p>
              </div>

              {/* Barra de progreso */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>{uploadProgress.percentage}%</span>
                  <span>{formatFileSize(uploadProgress.loaded)} / {formatFileSize(uploadProgress.total)}</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-purple-600 h-full transition-all duration-300 ease-out flex items-center justify-end"
                    style={{ width: `${uploadProgress.percentage}%` }}
                  >
                    {uploadProgress.percentage > 10 && (
                      <div className="w-2 h-full bg-white opacity-50 animate-pulse"></div>
                    )}
                  </div>
                </div>
              </div>

              {/* Estadísticas */}
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

              {/* Información adicional */}
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

          {/* Advertencia */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3">
            <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>
                El archivo se validará automáticamente. Si no contiene la estructura correcta, será rechazado.
              </span>
            </p>
          </div>
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

// Modal de restauración
function RestoreModal({ backup, onClose, onConfirm }) {
  const [confirmText, setConfirmText] = useState('');
  const [understood, setUnderstood] = useState(false);
  
  const canConfirm = understood && confirmText === 'RESTAURAR';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Restaurar Backup de Producción
            </h3>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Advertencia principal */}
          <div className="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-2 text-sm text-red-800 dark:text-red-200">
                <p className="font-semibold">⚠️ ADVERTENCIA CRÍTICA</p>
                <p>Esta operación es <strong>IRREVERSIBLE</strong> y afectará el sistema de producción:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>El servicio de Odoo se <strong>detendrá</strong> (~2-5 minutos de inactividad)</li>
                  <li>Se creará un backup de seguridad automático antes de restaurar</li>
                  <li>La base de datos actual será <strong>REEMPLAZADA COMPLETAMENTE</strong></li>
                  <li>Todos los archivos del filestore serán <strong>REEMPLAZADOS</strong></li>
                  <li>Se perderán todos los cambios realizados después de este backup</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Información del backup */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
              📦 Backup a restaurar:
            </p>
            <div className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
              <p><strong>Archivo:</strong> {backup.filename}</p>
              <p><strong>Fecha:</strong> {backup.date}</p>
              <p><strong>Tamaño:</strong> {backup.size_human}</p>
            </div>
          </div>

          {/* Proceso de restauración */}
          <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              🔄 Proceso de restauración:
            </p>
            <ol className="space-y-1 text-sm text-gray-700 dark:text-gray-300 list-decimal list-inside">
              <li>Crear backup de seguridad del estado actual</li>
              <li>Detener servicio de Odoo</li>
              <li>Extraer y validar backup</li>
              <li>Restaurar base de datos</li>
              <li>Restaurar filestore</li>
              <li>Reiniciar servicio</li>
            </ol>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
              ℹ️ Si algo falla, el sistema se restaurará automáticamente al estado anterior.
            </p>
          </div>

          {/* Checkbox de confirmación */}
          <div className="space-y-3">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={understood}
                onChange={(e) => setUnderstood(e.target.checked)}
                className="mt-1 w-4 h-4 text-red-600 rounded"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Entiendo que esta operación reemplazará completamente el sistema de producción actual y que habrá tiempo de inactividad.
              </span>
            </label>

            {/* Input de confirmación */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Para confirmar, escribe <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded text-red-600 dark:text-red-400 font-mono">RESTAURAR</code>
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="Escribe RESTAURAR"
                className="w-full px-4 py-2 border-2 border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:border-red-500 focus:ring-2 focus:ring-red-500"
                disabled={!understood}
              />
            </div>
          </div>
        </div>

        <div className="flex gap-3 p-6 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={!canConfirm}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
          >
            🔄 Restaurar Backup
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal de log
function LogModal({ log, onClose, title = "Log" }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        </div>

        <div className="flex-1 overflow-auto p-6">
          <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
            {log || 'Esperando...'}
          </pre>
        </div>

        <div className="p-6 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
