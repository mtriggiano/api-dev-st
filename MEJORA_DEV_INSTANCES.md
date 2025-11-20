# ✅ Mejora: Selección de Instancia de Producción para Desarrollo

## 🎯 Objetivo

Permitir que al crear una instancia de desarrollo, se pueda elegir de qué instancia de producción se va a clonar, en lugar de usar siempre la misma instancia hardcodeada.

## 🔧 Cambios Implementados

### 1. Script de Creación de Desarrollo

**Archivo**: `/home/mtg/api-dev/scripts/odoo/create-dev-instance.sh`

**Cambios**:
- ✅ Acepta segundo argumento: instancia de producción a clonar
- ✅ Si no se pasa argumento, lista las instancias disponibles y pregunta
- ✅ Detecta automáticamente si solo hay una instancia
- ✅ Valida que la instancia seleccionada existe
- ✅ Lee el nombre de la BD del `odoo.conf` de la instancia

**Uso**:
```bash
# Con instancia específica
./create-dev-instance.sh nombre-dev prod-panel3

# Sin instancia (pregunta interactivamente)
./create-dev-instance.sh nombre-dev
```

### 2. Backend - Instance Manager

**Archivo**: `/home/mtg/api-dev/backend/services/instance_manager.py`

**Nuevo método**:
```python
def list_production_instances(self):
    """Lista solo las instancias de producción válidas para clonar"""
```

**Método modificado**:
```python
def create_dev_instance(self, name, source_instance=None):
    """Crea una nueva instancia de desarrollo
    
    Args:
        name: Nombre de la instancia de desarrollo
        source_instance: Instancia de producción a clonar (opcional)
    """
```

### 3. Backend - API Routes

**Archivo**: `/home/mtg/api-dev/backend/routes/instances.py`

**Nueva ruta**:
```python
@instances_bp.route('/production-instances', methods=['GET'])
def get_production_instances():
    """Lista las instancias de producción disponibles para clonar"""
```

**Ruta modificada**:
```python
@instances_bp.route('/create', methods=['POST'])
# Ahora acepta 'sourceInstance' en el body
```

## 📋 Pendiente: Actualización del Frontend

### Archivos a Modificar

#### 1. `/home/mtg/api-dev/frontend/src/lib/api.js`

Agregar método para obtener instancias de producción:

```javascript
// En el objeto instances
getProductionInstances: () => api.get('/instances/production-instances'),

// Modificar el método create para aceptar sourceInstance
create: (name, sourceInstance = null) => 
  api.post('/instances/create', { name, sourceInstance }),
```

#### 2. `/home/mtg/api-dev/frontend/src/components/Instances.jsx`

**Agregar estados**:
```javascript
const [productionInstances, setProductionInstances] = useState([]);
const [selectedSourceInstance, setSelectedSourceInstance] = useState('');
```

**Cargar instancias de producción al abrir el modal**:
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
  }
};
```

**Modificar handleCreateInstance**:
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
    // ... resto del código
  }
};
```

**Agregar selector en el modal**:
```jsx
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
      </div>
      
      {/* Input de nombre */}
      <input
        type="text"
        value={newInstanceName}
        onChange={(e) => setNewInstanceName(e.target.value)}
        placeholder="Nombre (ej: juan, testing, feature-xyz)"
        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
      />
      
      {/* Resto del modal... */}
    </div>
  </div>
)}
```

## 🧪 Pruebas

### Desde Línea de Comandos

```bash
# Listar instancias disponibles y preguntar
cd /home/mtg/api-dev/scripts/odoo
./create-dev-instance.sh midev

# Especificar instancia directamente
./create-dev-instance.sh midev prod-panel3
```

### Desde Panel Web (después de actualizar frontend)

1. Ir a "Instancias"
2. Clic en "Nueva Instancia Dev"
3. **Ver selector con instancias de producción disponibles**
4. Seleccionar instancia a clonar
5. Ingresar nombre
6. Crear

## 📊 Ejemplo de Flujo

```
Usuario crea instancia de desarrollo "juan"
↓
Frontend muestra selector con:
  - chekmart
  - ciac
  - prod-panel3
  - prod-panel1sudo
↓
Usuario selecciona "prod-panel3"
↓
Backend ejecuta: ./create-dev-instance.sh juan prod-panel3
↓
Script clona desde prod-panel3
↓
Crea: dev-juan con BD dev-juan-prod-panel3
```

## ✅ Beneficios

1. **Flexibilidad**: Cada desarrollador puede clonar la instancia que necesite
2. **Múltiples clientes**: Si tienes varios clientes en producción, puedes clonar el que necesites
3. **Testing específico**: Puedes probar cambios sobre datos de clientes específicos
4. **Sin hardcoding**: Ya no depende de `PROD_INSTANCE_NAME` del `.env`

## 🎯 Estado Actual

- ✅ Script modificado y funcionando
- ✅ Backend actualizado y probado
- ✅ API endpoints creados
- ⏳ Frontend pendiente de actualización

## 📝 Próximos Pasos

1. Actualizar `frontend/src/lib/api.js` con los nuevos métodos
2. Actualizar `frontend/src/components/Instances.jsx` con el selector
3. Compilar frontend: `npm run build`
4. Probar desde el panel web

---

**Última actualización**: 18 Nov 2025 22:35
**Estado**: Backend completo, Frontend pendiente
