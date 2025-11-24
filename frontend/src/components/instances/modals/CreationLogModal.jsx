/**
 * Modal para mostrar el log de creación de instancias en tiempo real
 */
export default function CreationLogModal({ creationLog, creationLogRef, onClose }) {
  if (!creationLog.show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Creando instancia: {creationLog.instanceName}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3 mb-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            ⏳ La creación puede tardar varios minutos. El log se actualiza automáticamente.
          </p>
        </div>
        <pre 
          ref={creationLogRef} 
          className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto flex-1 text-sm font-mono whitespace-pre-wrap"
        >
          {creationLog.log}
        </pre>
      </div>
    </div>
  );
}
