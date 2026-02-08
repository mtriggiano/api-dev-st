import { useState, useEffect } from 'react';
import { Server, RefreshCw, Database, FileText, FolderSync, Palette, Trash2, Eye, Github, GitCommit, Settings, Terminal } from 'lucide-react';
import { github } from '../../../lib/api';

/**
 * Tarjeta de instancia individual con información y acciones
 */
export default function InstanceCard({ 
  instance, 
  onAction, 
  onViewLogs, 
  onGitHub, 
  onOpenLogViewer,
  actionLoading, 
  isProduction 
}) {
  const statusColor = instance.status === 'active' ? 'text-green-600' : 'text-red-600';
  const statusBg = instance.status === 'active' ? 'bg-green-100 dark:bg-green-900' : 'bg-red-100 dark:bg-red-900';
  const [currentCommit, setCurrentCommit] = useState(null);
  const [loadingCommit, setLoadingCommit] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  // Cargar commit actual cuando el componente se monta
  useEffect(() => {
    loadCurrentCommit();
  }, [instance.name]);

  const loadCurrentCommit = async () => {
    setLoadingCommit(true);
    try {
      const response = await github.getCurrentCommit(instance.name);
      if (response.data.success) {
        setCurrentCommit(response.data.commit);
      }
    } catch (error) {
      // Silenciosamente fallar si no hay config de Git
      console.log('No Git config for', instance.name);
    } finally {
      setLoadingCommit(false);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow relative">
      {/* Botón GitHub en esquina superior derecha - para todas las instancias */}
      <div className="absolute top-4 right-4 flex flex-col items-end gap-2">
        <button
          onClick={() => onGitHub(instance.name)}
          title="Conectar con GitHub para control de versiones"
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors border border-gray-300 dark:border-gray-600"
        >
          <Github className="w-4 h-4" />
          <span className="hidden sm:inline">GitHub</span>
        </button>
        
        {/* Mostrar commit actual si existe */}
        {currentCommit && (
          <div className="flex items-center gap-2 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 rounded border border-gray-300 dark:border-gray-600">
            <GitCommit className="w-3 h-3 text-gray-600 dark:text-gray-400" />
            <span className="font-mono text-gray-700 dark:text-gray-300" title={currentCommit.message}>
              {currentCommit.short_hash}
            </span>
          </div>
        )}
      </div>
      
      {/* Header con info */}
      <div className="flex items-start gap-3 mb-4 pr-24">
        <div className={`${statusBg} p-2 rounded-lg flex-shrink-0`}>
          <Server className={`w-6 h-6 ${statusColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-semibold text-gray-900 dark:text-white">{instance.name}</h4>
            <span className={`px-2 py-1 text-xs rounded-full ${statusBg} ${statusColor}`}>
              {instance.status}
            </span>
          </div>
          <div className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-300">
            {instance.domain && (
              <p className="truncate">🌐 <a href={`https://${instance.domain}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">{instance.domain}</a></p>
            )}
            {instance.port && <p>🔌 Puerto: {instance.port}</p>}
            {instance.database && <p className="truncate">🗄️ BD: {instance.database}</p>}
          </div>
        </div>
      </div>

      {/* Botones de acción - responsive */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onAction('restart', instance.name)}
          disabled={actionLoading[`restart-${instance.name}`]}
          title="Reiniciar el servicio Odoo de esta instancia"
          className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${actionLoading[`restart-${instance.name}`] ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Reiniciar</span>
        </button>
        
        {!isProduction && (
          <>
            <button
              onClick={() => onAction('update-db', instance.name)}
              disabled={actionLoading[`update-db-${instance.name}`]}
              title="Actualizar la base de datos desde producción (incluye filestore)"
              className="flex items-center gap-2 px-3 py-2 text-sm text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <Database className="w-4 h-4" />
              <span className="hidden sm:inline">BD</span>
            </button>
            <button
              onClick={() => onAction('update-files', instance.name)}
              disabled={actionLoading[`update-files-${instance.name}`]}
              title="Actualizar el código fuente de Odoo desde producción"
              className="flex items-center gap-2 px-3 py-2 text-sm text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <FileText className="w-4 h-4" />
              <span className="hidden sm:inline">Archivos</span>
            </button>
            <button
              onClick={() => onAction('sync-filestore', instance.name)}
              disabled={actionLoading[`sync-filestore-${instance.name}`]}
              title="Sincronizar solo el filestore (imágenes, PDFs, assets) desde producción"
              className="flex items-center gap-2 px-3 py-2 text-sm text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <FolderSync className="w-4 h-4" />
              <span className="hidden sm:inline">Filestore</span>
            </button>
            <button
              onClick={() => onAction('regenerate-assets', instance.name)}
              disabled={actionLoading[`regenerate-assets-${instance.name}`]}
              title="Regenerar assets (CSS, JS, iconos) de Odoo"
              className="flex items-center gap-2 px-3 py-2 text-sm text-pink-600 dark:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <Palette className="w-4 h-4" />
              <span className="hidden sm:inline">Assets</span>
            </button>
            <button
              onClick={() => onAction('delete', instance.name)}
              disabled={actionLoading[`delete-${instance.name}`]}
              title="Eliminar permanentemente esta instancia de desarrollo"
              className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              <span className="hidden sm:inline">Eliminar</span>
            </button>
          </>
        )}
        
        <button
          onClick={() => onOpenLogViewer(instance.name)}
          title="Visor de logs Odoo con colores y filtros"
          className="flex items-center gap-2 px-3 py-2 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg transition-colors"
        >
          <Terminal className="w-4 h-4" />
          <span className="hidden sm:inline">Logs</span>
        </button>
        
        {isProduction && (
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              title="Opciones de la instancia"
              className="p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
            </button>
            
            {showMenu && (
              <>
                {/* Overlay para cerrar el menú al hacer clic fuera */}
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setShowMenu(false)}
                />
                
                {/* Menú desplegable */}
                <div className="absolute right-0 bottom-full mb-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      window.location.href = `/backups-v2?instance=${encodeURIComponent(instance.name)}`;
                    }}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors rounded-t-lg"
                  >
                    <Database className="w-4 h-4" />
                    <span>Configurar Backups</span>
                  </button>
                  <div className="border-t border-gray-200 dark:border-gray-700"></div>
                  <button
                    onClick={() => {
                      setShowMenu(false);
                      onAction('delete-production', instance.name);
                    }}
                    disabled={actionLoading[`delete-prod-${instance.name}`]}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Eliminar Instancia</span>
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
