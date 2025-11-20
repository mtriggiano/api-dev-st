# Cambios para Instances.jsx

## 1. Agregar nuevos estados (después de la línea 16)

```javascript
const [sslMethod, setSslMethod] = useState('letsencrypt');
const [productionInstances, setProductionInstances] = useState([]); // NUEVO
const [selectedSourceInstance, setSelectedSourceInstance] = useState(''); // NUEVO
const [selectedInstance, setSelectedInstance] = useState(null);
```

## 2. Modificar handleCreateInstance (línea 136-176)

Reemplazar la función completa con:

```javascript
const handleCreateInstance = async () => {
  if (!newInstanceName.trim()) {
    setToast({ show: true, message: 'Debes ingresar un nombre para la instancia', type: 'warning' });
    return;
  }

  setActionLoading({ create: true });
  try {
    // Pasar la instancia de producción seleccionada
    const response = await instances.create(newInstanceName, selectedSourceInstance);
    setShowCreateModal(false);
    setCreationLog({ show: true, instanceName: newInstanceName, log: 'Iniciando creación...\n' });
    
    // Polling del log cada 2 segundos
    const logInterval = setInterval(async () => {
      try {
        const logResponse = await instances.getCreationLog(newInstanceName);
        setCreationLog(prev => ({ ...prev, log: logResponse.data.log || 'Esperando...' }));
        
        // Si el log contiene "✅" (checkmark) significa que terminó
        if (logResponse.data.log && logResponse.data.log.includes('✅ Instancia')) {
          clearInterval(logInterval);
          setTimeout(() => {
            setCreationLog({ show: false, instanceName: '', log: '' });
            setToast({ show: true, message: 'Instancia creada exitosamente', type: 'success' });
            fetchInstances();
          }, 3000);
        }
      } catch (err) {
        console.error('Error fetching log:', err);
      }
    }, 2000);
    
    setNewInstanceName('');
  } catch (error) {
    setToast({ show: true, message: error.response?.data?.error || 'Error al crear la instancia', type: 'error' });
  } finally {
    setActionLoading({ create: false });
  }
};
```

## 3. Agregar función para abrir modal y cargar instancias (después de handleCreateInstance)

```javascript
const handleOpenCreateModal = async () => {
  setShowCreateModal(true);
  try {
    const response = await instances.getProductionInstances();
    setProductionInstances(response.data.instances || []);
    // Seleccionar la primera por defecto
    if (response.data.instances && response.data.instances.length > 0) {
      setSelectedSourceInstance(response.data.instances[0].name);
    }
  } catch (error) {
    console.error('Error cargando instancias de producción:', error);
    setToast({ show: true, message: 'Error cargando instancias de producción', type: 'error' });
  }
};
```

## 4. Modificar el botón "Nueva Instancia Dev" (línea ~320)

Cambiar:
```javascript
onClick={() => setShowCreateModal(true)}
```

Por:
```javascript
onClick={handleOpenCreateModal}
```

## 5. Modificar el modal de creación (línea ~346)

Reemplazar todo el modal con:

```javascript
{/* Modal de creación */}
{showCreateModal && (
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
        <select
          value={selectedSourceInstance}
          onChange={(e) => setSelectedSourceInstance(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          {productionInstances.map((instance) => (
            <option key={instance.name} value={instance.name}>
              {instance.name} {instance.domain ? `(${instance.domain})` : ''}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Se clonará la base de datos y archivos de esta instancia
        </p>
      </div>
      
      {/* Input de nombre */}
      <input
        type="text"
        value={newInstanceName}
        onChange={(e) => setNewInstanceName(e.target.value)}
        placeholder="Nombre (ej: juan, testing, feature-xyz)"
        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      />
      
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4">
        <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>La creación puede tardar varios minutos. Se clonará desde {selectedSourceInstance || 'producción'} y se neutralizará automáticamente.</span>
        </p>
      </div>
      
      <div className="flex gap-3">
        <button
          onClick={handleCreateInstance}
          disabled={actionLoading.create}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {actionLoading.create ? 'Creando...' : 'Crear'}
        </button>
        <button
          onClick={() => setShowCreateModal(false)}
          className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>
  </div>
)}
```

## Resumen de cambios

1. ✅ Agregar estados: `productionInstances`, `selectedSourceInstance`
2. ✅ Modificar `handleCreateInstance` para pasar `selectedSourceInstance`
3. ✅ Agregar función `handleOpenCreateModal` para cargar instancias
4. ✅ Cambiar botón para usar `handleOpenCreateModal`
5. ✅ Modificar modal para incluir selector de instancia

## Aplicar cambios

Edita el archivo `/home/mtg/api-dev/frontend/src/components/Instances.jsx` y aplica estos cambios.
