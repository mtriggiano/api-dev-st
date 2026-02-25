import { AlertCircle, GitBranch, Search } from 'lucide-react';
import { useState, useMemo } from 'react';

/**
 * Modal para crear instancias de desarrollo
 */
export default function CreateDevModal({
  show,
  onClose,
  onCreate,
  newInstanceName,
  setNewInstanceName,
  selectedSourceInstance,
  setSelectedSourceInstance,
  neutralizeDatabase,
  setNeutralizeDatabase,
  gitBranch,
  setGitBranch,
  productionInstances,
  actionLoading
}) {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Filtrar instancias de producción según búsqueda
  const filteredInstances = useMemo(() => {
    if (!searchTerm.trim()) return productionInstances;
    
    const search = searchTerm.toLowerCase();
    return productionInstances.filter(instance => 
      instance.name.toLowerCase().includes(search) ||
      (instance.domain && instance.domain.toLowerCase().includes(search))
    );
  }, [productionInstances, searchTerm]);
  
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Crear Nueva Instancia de Desarrollo
        </h3>
        
        {/* Selector de instancia de producción */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Clonar desde:
          </label>
          
          {/* Campo de búsqueda */}
          <div className="relative mb-2">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar instancia..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400"
            />
          </div>
          
          {/* Selector con instancias filtradas */}
          <select
            value={selectedSourceInstance}
            onChange={(e) => setSelectedSourceInstance(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            size={Math.min(filteredInstances.length, 6)}
          >
            {filteredInstances.length > 0 ? (
              filteredInstances.map((instance) => (
                <option key={instance.name} value={instance.name}>
                  {instance.name} {instance.domain ? `(${instance.domain})` : ''}
                </option>
              ))
            ) : (
              <option disabled>No se encontraron instancias</option>
            )}
          </select>
          
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {filteredInstances.length} de {productionInstances.length} instancias
            {searchTerm && ` · Filtrando por "${searchTerm}"`}
          </p>
        </div>
        
        {/* Input de nombre */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Nombre de la instancia
          </label>
          <input
            type="text"
            value={newInstanceName}
            onChange={(e) => setNewInstanceName(e.target.value)}
            placeholder="Nombre (ej: juan, testing, feature-xyz)"
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
        </div>
        
        {/* Campo de rama Git */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
            <GitBranch className="w-4 h-4" />
            Rama Git (opcional)
          </label>
          <input
            type="text"
            value={gitBranch}
            onChange={(e) => setGitBranch(e.target.value)}
            placeholder={`Dejar vacío para usar: dev-${newInstanceName || 'nombre'}`}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Si configuras Git después, esta será la rama por defecto (ej: develop, feature/test)
          </p>
        </div>
        
        {/* Checkbox de neutralización */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={neutralizeDatabase}
              onChange={(e) => setNeutralizeDatabase(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Neutralizar base de datos
            </span>
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 ml-6">
            {neutralizeDatabase 
              ? '✅ Se desactivarán crons, correos, webhooks y se eliminará la licencia Enterprise'
              : '⚠️  La instancia mantendrá todos los datos y configuraciones de producción'
            }
          </p>
        </div>
        
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4">
          <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>La creación puede tardar varios minutos. Se clonará desde {selectedSourceInstance || 'producción'}.</span>
          </p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onCreate}
            disabled={actionLoading.create}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            {actionLoading.create ? 'Creando...' : 'Crear'}
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
