/**
 * Modal para mostrar el log de actualización de instancias en tiempo real
 */
export default function UpdateLogModal({ updateLog, updateLogRef, onClose }) {
  if (!updateLog.show) return null;

  const actionNames = {
    'update-db': 'Actualización de Base de Datos',
    'update-files': 'Actualización de Archivos',
    'sync-filestore': 'Sincronización de Filestore',
    'regenerate-assets': 'Regeneración de Assets'
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {actionNames[updateLog.action] || updateLog.action}: {updateLog.instanceName}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>
        {!updateLog.completed ? (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3 mb-4">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              ⏳ La actualización puede tardar varios minutos. El log se actualiza automáticamente.
            </p>
          </div>
        ) : (
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3 mb-4">
            <p className="text-sm text-green-800 dark:text-green-200">
              ✅ Actualización completada. Puedes cerrar este modal.
            </p>
          </div>
        )}
        <pre 
          ref={updateLogRef} 
          className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto flex-1 text-sm font-mono whitespace-pre-wrap"
        >
          {updateLog.log}
        </pre>
      </div>
    </div>
  );
}
