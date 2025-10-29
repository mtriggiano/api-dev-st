import { useState, useEffect } from 'react';
import { backup } from '../lib/api';
import { Database, Download, Trash2, RefreshCw, Settings, HardDrive, Calendar, Clock, AlertCircle } from 'lucide-react';
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

// Modal de log
function LogModal({ log, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Log de Backup</h3>
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
