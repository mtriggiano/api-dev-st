import { useState, useEffect, useRef } from 'react';
import { instances, github } from '../lib/api';
import { Server, Play, Square, Trash2, RefreshCw, Database, FileText, Plus, Eye, AlertCircle, FolderSync, Palette, Github, GitCommit, Clock, Settings, MoreVertical, Search, Filter } from 'lucide-react';
import ConfirmModal from './ConfirmModal';
import Toast from './Toast';
import GitHubModal from './GitHubModal';

// Modales refactorizados
import { CreationLogModal, UpdateLogModal, CreateDevModal, CreateProdModal, LogsModal } from './instances/modals';
// Hooks personalizados
import { useInstances, useCreationLog, useUpdateLog } from './instances/hooks';
// Componentes de tarjetas
import { InstanceCard } from './instances/cards';

export default function Instances() {
  // Hook para manejar lista de instancias (reemplaza useState y useEffect)
  const { instanceList, loading, fetchInstances } = useInstances();
  
  // Hook para manejar log de creación (reemplaza useState, useEffect y polling)
  const { creationLog, creationLogRef, startPolling: startCreationPolling, closeLog: closeCreationLog } = useCreationLog();
  
  // Hook para manejar log de actualización (reemplaza useState, useEffect y polling)
  const { updateLog, updateLogRef, startPolling: startUpdatePolling, closeLog: closeUpdateLog } = useUpdateLog();
  const [actionLoading, setActionLoading] = useState({});
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateProdModal, setShowCreateProdModal] = useState(false);
  const [newInstanceName, setNewInstanceName] = useState('');
  const [newProdInstanceName, setNewProdInstanceName] = useState('');
  const [odooVersion, setOdooVersion] = useState('19');
  const [odooEdition, setOdooEdition] = useState('enterprise');
  const [sslMethod, setSslMethod] = useState('letsencrypt');
  const [availableProductionInstances, setAvailableProductionInstances] = useState([]);
  const [selectedSourceInstance, setSelectedSourceInstance] = useState('');
  const [neutralizeDatabase, setNeutralizeDatabase] = useState(true);
  const [selectedInstance, setSelectedInstance] = useState(null);
  const [logs, setLogs] = useState('');
  const [activeLogTab, setActiveLogTab] = useState('systemd');
  const [logsLoading, setLogsLoading] = useState(false);
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, action: null, instanceName: null, neutralize: true });
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [restartModal, setRestartModal] = useState({ show: false, instanceName: '', status: 'Reiniciando...' });
  const [githubModal, setGithubModal] = useState({ show: false, instanceName: '' });
  const [deleteProductionModal, setDeleteProductionModal] = useState({ show: false, instanceName: '', confirmation: '', step: 1 });
  const [filterByProduction, setFilterByProduction] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Los hooks ya manejan: fetchInstances, creationLog, updateLog, refs y auto-scroll

  const showConfirmation = (action, instanceName) => {
    // Por defecto, neutralizar en update-db
    const neutralize = action === 'update-db' ? true : false;
    setConfirmModal({ isOpen: true, action, instanceName, neutralize });
  };

  const handleAction = async (action, instanceName) => {
    setActionLoading({ ...actionLoading, [`${action}-${instanceName}`]: true });
    
    try {
      let response;
      
      // Para update-db, update-files, sync-filestore y regenerate-assets, mostrar modal con log
      if (action === 'update-db' || action === 'update-files' || action === 'sync-filestore' || action === 'regenerate-assets') {
        response = action === 'update-db' 
          ? await instances.updateDb(instanceName, confirmModal.neutralize)
          : action === 'update-files'
          ? await instances.updateFiles(instanceName)
          : action === 'sync-filestore'
          ? await instances.syncFilestore(instanceName)
          : await instances.regenerateAssets(instanceName);
        
        if (response.data.success) {
          // Usar hook para manejar el polling del log
          startUpdatePolling(instanceName, action);
          fetchInstances();
        }
      } else if (action === 'restart') {
        // Para reiniciar, mostrar modal con estado
        setRestartModal({ show: true, instanceName, status: 'Deteniendo servicio...' });
        
        response = await instances.restart(instanceName);
        
        if (response.data.success) {
          setRestartModal(prev => ({ ...prev, status: 'Iniciando servicio...' }));
          
          // Esperar un momento y verificar estado
          setTimeout(async () => {
            setRestartModal(prev => ({ ...prev, status: '\u2705 Servicio reiniciado correctamente' }));
            
            setTimeout(() => {
              setRestartModal({ show: false, instanceName: '', status: '' });
              setToast({ show: true, message: 'Instancia reiniciada correctamente', type: 'success' });
              fetchInstances();
            }, 2000);
          }, 2000);
        }
      } else if (action === 'delete-production') {
        // Para eliminar producción, abrir modal de doble confirmación
        handleDeleteProduction(instanceName);
        return; // No continuar con el flujo normal
      } else {
        // Para delete y otras acciones
        switch (action) {
          case 'delete':
            response = await instances.delete(instanceName);
            break;
          default:
            break;
        }
        
        if (response) {
          setToast({ show: true, message: response.data.message || 'Acci\u00f3n completada', type: 'success' });
          fetchInstances();
        }
      }
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al ejecutar la acci\u00f3n', type: 'error' });
    } finally {
      setActionLoading({ ...actionLoading, [`${action}-${instanceName}`]: false });
    }
  };

  const handleDeleteProduction = async (instanceName) => {
    setDeleteProductionModal({ show: true, instanceName, confirmation: '', step: 1 });
  };

  const handleConfirmDeleteProduction = async () => {
    const { instanceName, confirmation } = deleteProductionModal;
    const expectedConfirmation = `BORRAR${instanceName}`;
    
    if (confirmation !== expectedConfirmation) {
      setToast({ show: true, message: `Debes escribir exactamente: ${expectedConfirmation}`, type: 'error' });
      return;
    }

    setActionLoading({ ...actionLoading, [`delete-prod-${instanceName}`]: true });
    try {
      const response = await instances.deleteProduction(instanceName, confirmation);
      setDeleteProductionModal({ show: false, instanceName: '', confirmation: '', step: 1 });
      setToast({ show: true, message: response.data.message || 'Instancia de producción eliminada', type: 'success' });
      fetchInstances();
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al eliminar la instancia', type: 'error' });
    } finally {
      setActionLoading({ ...actionLoading, [`delete-prod-${instanceName}`]: false });
    }
  };

  const handleCreateInstance = async () => {
    if (!newInstanceName.trim()) {
      setToast({ show: true, message: 'Debes ingresar un nombre para la instancia', type: 'warning' });
      return;
    }

    setActionLoading({ create: true });
    try {
      const response = await instances.create(newInstanceName, selectedSourceInstance, neutralizeDatabase);
      setShowCreateModal(false);
      
      // Usar hook para manejar el polling del log
      startCreationPolling(newInstanceName, false); // false = dev instance
      
      setNewInstanceName('');
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al crear la instancia', type: 'error' });
    } finally {
      setActionLoading({ create: false });
    }
  };

  const handleOpenCreateModal = async () => {
    setShowCreateModal(true);
    try {
      const response = await instances.getProductionInstances();
      setAvailableProductionInstances(response.data.instances || []);
      if (response.data.instances && response.data.instances.length > 0) {
        setSelectedSourceInstance(response.data.instances[0].name);
      }
    } catch (error) {
      console.error('Error cargando instancias de producción:', error);
      setToast({ show: true, message: 'Error cargando instancias de producción', type: 'error' });
    }
  };


  const handleCreateProdInstance = async () => {
    if (!newProdInstanceName.trim()) {
      setToast({ show: true, message: 'Debes ingresar un nombre para la instancia', type: 'warning' });
      return;
    }

    setActionLoading({ createProd: true });
    try {
      const response = await instances.createProduction(newProdInstanceName, odooVersion, odooEdition, sslMethod);
      setShowCreateProdModal(false);
      
      const instanceName = response.data.instance_name || `prod-${newProdInstanceName}`;
      
      // Usar hook para manejar el polling del log
      startCreationPolling(instanceName, true); // true = production instance
      
      setNewProdInstanceName('');
      setOdooVersion('19');
      setOdooEdition('enterprise');
      setSslMethod('letsencrypt');
    } catch (error) {
      setToast({ show: true, message: error.response?.data?.error || 'Error al crear la instancia de producción', type: 'error' });
    } finally {
      setActionLoading({ createProd: false });
    }
  };

  const handleViewLogs = async (instanceName, logType = 'systemd') => {
    setSelectedInstance(instanceName);
    setActiveLogTab(logType);
    setLogsLoading(true);
    setLogs('Cargando logs...');
    try {
      if (logType === 'git-deploy') {
        // Logs de Git/Deploy
        const response = await github.getDeployLogs(instanceName, 50);
        if (response.data.success && response.data.logs.length > 0) {
          const formattedLogs = response.data.logs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleString('es-AR');
            const status = log.status === 'success' ? '✅' : '❌';
            return `[${timestamp}] ${status} ${log.action}: ${log.details} (${log.user})`;
          }).join('\n');
          setLogs(formattedLogs);
        } else {
          setLogs('No hay logs de deploy disponibles');
        }
      } else {
        // Logs normales (systemd, odoo, nginx)
        const response = await instances.getLogs(instanceName, 200, logType);
        setLogs(response.data.logs);
      }
    } catch (error) {
      setLogs('Error al cargar logs: ' + (error.response?.data?.error || error.message));
    } finally {
      setLogsLoading(false);
    }
  };

  const handleLogTabChange = (logType) => {
    if (selectedInstance) {
      handleViewLogs(selectedInstance, logType);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Filtrar instancias
  let productionInstances = instanceList.filter(i => i.type === 'production');
  let developmentInstances = instanceList.filter(i => i.type === 'development');

  // Aplicar filtro por instancia de producción
  if (filterByProduction !== 'all') {
    // Mostrar solo la instancia de producción seleccionada
    productionInstances = productionInstances.filter(i => i.name === filterByProduction);
    
    // Mostrar solo las instancias de desarrollo que corresponden a esta producción
    // Las instancias dev tienen formato: dev-{nombre}-{produccion}
    developmentInstances = developmentInstances.filter(i => {
      // Extraer el nombre de la instancia de producción del nombre dev
      // Ejemplo: dev-testp4-prod-panel4 -> prod-panel4
      const match = i.database?.match(new RegExp(`dev-[^-]+-(.+)`));
      if (match) {
        const prodName = match[1];
        return prodName === filterByProduction;
      }
      return false;
    });
  }

  // Aplicar búsqueda por texto
  if (searchTerm.trim()) {
    const search = searchTerm.toLowerCase();
    productionInstances = productionInstances.filter(i => 
      i.name?.toLowerCase().includes(search) ||
      i.domain?.toLowerCase().includes(search) ||
      i.database?.toLowerCase().includes(search)
    );
    developmentInstances = developmentInstances.filter(i => 
      i.name?.toLowerCase().includes(search) ||
      i.domain?.toLowerCase().includes(search) ||
      i.database?.toLowerCase().includes(search)
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Instancias Odoo</h2>
          <p className="text-gray-600 dark:text-gray-300 mt-1">Gestión de instancias de producción y desarrollo</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateProdModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Nueva Producción
          </button>
          <button
            onClick={handleOpenCreateModal}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Nueva Desarrollo
          </button>
        </div>
      </div>

      {/* Barra de filtros y búsqueda */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Filtro por instancia de producción */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Filter className="w-4 h-4 inline mr-2" />
              Filtrar por Instancia de Producción
            </label>
            <select
              value={filterByProduction}
              onChange={(e) => setFilterByProduction(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="all">Todas las instancias</option>
              {instanceList
                .filter(i => i.type === 'production')
                .map(prod => (
                  <option key={prod.name} value={prod.name}>
                    {prod.name} {prod.domain ? `(${prod.domain})` : ''}
                  </option>
                ))
              }
            </select>
          </div>

          {/* Buscador */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <Search className="w-4 h-4 inline mr-2" />
              Buscar
            </label>
            <div className="relative">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Buscar por nombre, dominio o base de datos..."
                className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Botón para limpiar filtros */}
          {(filterByProduction !== 'all' || searchTerm) && (
            <div className="flex items-end">
              <button
                onClick={() => {
                  setFilterByProduction('all');
                  setSearchTerm('');
                }}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors whitespace-nowrap"
              >
                Limpiar filtros
              </button>
            </div>
          )}
        </div>

        {/* Contador de resultados */}
        {(filterByProduction !== 'all' || searchTerm) && (
          <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
            Mostrando: {productionInstances.length} producción, {developmentInstances.length} desarrollo
          </div>
        )}
      </div>

      {/* Producción */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Producción</h3>
        </div>
        <div className="p-6">
          {productionInstances.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-300 text-center py-4">No hay instancias de producción</p>
          ) : (
            <div className="space-y-4">
              {productionInstances.map((instance) => (
                <InstanceCard
                  key={instance.name}
                  instance={instance}
                  onAction={showConfirmation}
                  onViewLogs={handleViewLogs}
                  onGitHub={(instanceName) => setGithubModal({ show: true, instanceName })}
                  actionLoading={actionLoading}
                  isProduction={true}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Desarrollo */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Desarrollo</h3>
        </div>
        <div className="p-6">
          {developmentInstances.length === 0 ? (
            <p className="text-gray-600 dark:text-gray-300 text-center py-4">No hay instancias de desarrollo</p>
          ) : (
            <div className="space-y-4">
              {developmentInstances.map((instance) => (
                <InstanceCard
                  key={instance.name}
                  instance={instance}
                  onAction={showConfirmation}
                  onViewLogs={handleViewLogs}
                  onGitHub={(instanceName) => setGithubModal({ show: true, instanceName })}
                  actionLoading={actionLoading}
                  isProduction={false}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de creación de desarrollo - Componente refactorizado */}
      <CreateDevModal
        show={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateInstance}
        newInstanceName={newInstanceName}
        setNewInstanceName={setNewInstanceName}
        selectedSourceInstance={selectedSourceInstance}
        setSelectedSourceInstance={setSelectedSourceInstance}
        neutralizeDatabase={neutralizeDatabase}
        setNeutralizeDatabase={setNeutralizeDatabase}
        productionInstances={productionInstances}
        actionLoading={actionLoading}
      />

      {/* Modal de creación de producción - Componente refactorizado */}
      <CreateProdModal
        show={showCreateProdModal}
        onClose={() => setShowCreateProdModal(false)}
        onCreate={handleCreateProdInstance}
        newProdInstanceName={newProdInstanceName}
        setNewProdInstanceName={setNewProdInstanceName}
        odooVersion={odooVersion}
        setOdooVersion={setOdooVersion}
        odooEdition={odooEdition}
        setOdooEdition={setOdooEdition}
        sslMethod={sslMethod}
        setSslMethod={setSslMethod}
        actionLoading={actionLoading}
      />

      {/* Modal de reinicio */}
      {restartModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <div className="flex flex-col items-center text-center">
              <div className="mb-4">
                <RefreshCw className="w-16 h-16 text-blue-600 animate-spin" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Reiniciando: {restartModal.instanceName}
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                {restartModal.status}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal de log de actualización */}
      <UpdateLogModal 
        updateLog={updateLog}
        updateLogRef={updateLogRef}
        onClose={closeUpdateLog}
      />

      {/* Modal de log de creación */}
      <CreationLogModal 
        creationLog={creationLog}
        creationLogRef={creationLogRef}
        onClose={closeCreationLog}
      />

      {/* Modal de logs - Componente refactorizado */}
      <LogsModal
        show={!!selectedInstance}
        instanceName={selectedInstance}
        activeLogTab={activeLogTab}
        logs={logs}
        logsLoading={logsLoading}
        onClose={() => setSelectedInstance(null)}
        onTabChange={handleLogTabChange}
      />

      {/* Modal de confirmación */}
      <ConfirmModal
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: null, instanceName: null, neutralize: true })}
        onConfirm={() => handleAction(confirmModal.action, confirmModal.instanceName)}
        title={getConfirmTitle(confirmModal.action)}
        message={getConfirmMessage(confirmModal.action, confirmModal.instanceName)}
        confirmText="Confirmar"
        cancelText="Cancelar"
        type={confirmModal.action === 'delete' ? 'danger' : 'warning'}
        showNeutralizeOption={confirmModal.action === 'update-db'}
        neutralize={confirmModal.neutralize}
        onNeutralizeChange={(value) => setConfirmModal({ ...confirmModal, neutralize: value })}
      />

      {/* Toast de notificaciones */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast({ show: false, message: '', type: 'success' })}
        />
      )}

      {/* Modal de GitHub */}
      <GitHubModal
        isOpen={githubModal.show}
        onClose={() => setGithubModal({ show: false, instanceName: '' })}
        instanceName={githubModal.instanceName}
        onSuccess={() => {
          setToast({ show: true, message: 'GitHub conectado exitosamente', type: 'success' });
        }}
      />

      {/* Modal de eliminación de producción con doble confirmación */}
      {deleteProductionModal.show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-red-100 dark:bg-red-900 p-3 rounded-full">
                <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Eliminar Instancia de Producción
              </h3>
            </div>

            {deleteProductionModal.step === 1 ? (
              <>
                <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm text-red-800 dark:text-red-200 font-semibold mb-2">
                    ⚠️ ADVERTENCIA: Esta acción es IRREVERSIBLE
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300">
                    Estás a punto de eliminar la instancia de producción <strong>{deleteProductionModal.instanceName}</strong>.
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-2">
                    Esto eliminará:
                  </p>
                  <ul className="text-sm text-red-700 dark:text-red-300 list-disc list-inside mt-1 space-y-1">
                    <li>La base de datos completa</li>
                    <li>Todos los archivos y código</li>
                    <li>El filestore (imágenes, PDFs, etc.)</li>
                    <li>La configuración de Nginx</li>
                    <li>El servicio systemd</li>
                  </ul>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteProductionModal({ show: false, instanceName: '', confirmation: '', step: 1 })}
                    className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={() => setDeleteProductionModal({ ...deleteProductionModal, step: 2 })}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Continuar
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                  Para confirmar la eliminación, escribe exactamente:
                </p>
                <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                  <code className="text-sm font-mono text-gray-900 dark:text-white">
                    BORRAR{deleteProductionModal.instanceName}
                  </code>
                </div>
                <input
                  type="text"
                  value={deleteProductionModal.confirmation}
                  onChange={(e) => setDeleteProductionModal({ ...deleteProductionModal, confirmation: e.target.value })}
                  placeholder={`BORRAR${deleteProductionModal.instanceName}`}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
                  autoFocus
                />
                <div className="flex gap-3">
                  <button
                    onClick={() => setDeleteProductionModal({ show: false, instanceName: '', confirmation: '', step: 1 })}
                    className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white px-4 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleConfirmDeleteProduction}
                    disabled={actionLoading[`delete-prod-${deleteProductionModal.instanceName}`] || deleteProductionModal.confirmation !== `BORRAR${deleteProductionModal.instanceName}`}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {actionLoading[`delete-prod-${deleteProductionModal.instanceName}`] ? 'Eliminando...' : 'Eliminar Definitivamente'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function getConfirmTitle(action) {
  const titles = {
    restart: 'Reiniciar Instancia',
    'update-db': 'Actualizar Base de Datos',
    'update-files': 'Actualizar Archivos',
    'sync-filestore': 'Sincronizar Filestore',
    'regenerate-assets': 'Regenerar Assets',
    delete: 'Eliminar Instancia'
  };
  return titles[action] || 'Confirmar Acción';
}

function getConfirmMessage(action, instanceName) {
  const messages = {
    restart: `¿Deseas reiniciar la instancia ${instanceName}? El servicio se detendrá temporalmente.`,
    'update-db': `¿Actualizar la base de datos de ${instanceName} desde producción? Esta operación puede tardar varios minutos.`,
    'update-files': `¿Actualizar los archivos de ${instanceName} desde producción?`,
    'sync-filestore': `¿Sincronizar el filestore (imágenes y archivos) de ${instanceName} desde producción? Esto copiará todos los assets.`,
    'regenerate-assets': `¿Regenerar los assets (CSS, JS, iconos) de ${instanceName}? El servicio se detendrá temporalmente.`,
    delete: `¿Estás seguro de eliminar la instancia ${instanceName}? Esta acción no se puede deshacer y se perderán todos los datos.`
  };
  return messages[action] || '¿Deseas continuar con esta acción?';
}

// InstanceCard ahora está en ./instances/cards/InstanceCard.jsx