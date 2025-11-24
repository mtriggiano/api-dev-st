/**
 * Modal para visualizar logs de instancias
 * Soporta múltiples tipos de logs: systemd, odoo, nginx-access, nginx-error, git-deploy
 */
export default function LogsModal({ 
  show, 
  instanceName, 
  activeLogTab, 
  logs, 
  logsLoading, 
  onClose, 
  onTabChange 
}) {
  if (!show) return null;

  const logTabs = [
    { id: 'systemd', label: 'Systemd Journal' },
    { id: 'odoo', label: 'Odoo Log' },
    { id: 'nginx-access', label: 'Nginx Access' },
    { id: 'nginx-error', label: 'Nginx Error' },
    { id: 'git-deploy', label: 'Git/Deploy' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Logs: {instanceName}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          >
            ✕
          </button>
        </div>
        
        {/* Pestañas de logs */}
        <div className="flex gap-2 mb-4 border-b border-gray-200 dark:border-gray-700">
          {logTabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 ${
                activeLogTab === tab.id
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        
        {/* Contenido del log */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {logsLoading ? (
            <div className="flex items-center justify-center flex-1">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto flex-1 text-sm font-mono">
              {logs}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
