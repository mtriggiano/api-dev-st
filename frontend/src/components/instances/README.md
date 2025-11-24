# Estructura Modular de Instances

Este directorio contiene la refactorización del componente `Instances.jsx` en módulos más pequeños y mantenibles.

## 📁 Estructura de Carpetas

```
instances/
├── hooks/              # Custom hooks para lógica reutilizable
│   ├── useInstances.js         # Manejo de lista de instancias
│   ├── useCreationLog.js       # Polling de logs de creación
│   ├── useUpdateLog.js         # Polling de logs de actualización
│   ├── useInstanceActions.js   # Acciones de instancias (start, stop, etc.)
│   └── index.js                # Exportaciones centralizadas
│
├── modals/             # Componentes de modales
│   ├── CreationLogModal.jsx    # Modal de log de creación
│   ├── UpdateLogModal.jsx      # Modal de log de actualización
│   ├── CreateDevModal.jsx      # Modal para crear instancia dev
│   ├── CreateProdModal.jsx     # Modal para crear instancia producción
│   ├── LogsModal.jsx           # Modal para ver logs (systemd, odoo, nginx)
│   ├── GitHubModal.jsx         # Modal de configuración GitHub (reusar existente)
│   └── index.js                # Exportaciones centralizadas
│
├── cards/              # Componentes de tarjetas
│   ├── InstanceCard.jsx        # Tarjeta de instancia individual
│   ├── InstanceActions.jsx     # Botones de acciones
│   └── index.js                # Exportaciones centralizadas
│
└── README.md           # Este archivo

```

## 🎯 Beneficios de la Refactorización

### 1. **Separación de Responsabilidades**
- **Hooks**: Lógica de negocio y estado
- **Modales**: UI de modales
- **Cards**: UI de tarjetas de instancias
- **Componente Principal**: Orquestación

### 2. **Reutilización**
- Los hooks pueden usarse en otros componentes
- Los modales son independientes y testeables
- Las tarjetas pueden mostrarse en diferentes contextos

### 3. **Mantenibilidad**
- Archivos más pequeños (< 200 líneas cada uno)
- Fácil localizar y modificar funcionalidad
- Menos conflictos en Git

### 4. **Testabilidad**
- Cada hook puede testearse independientemente
- Los modales pueden testearse con props mock
- Componentes más simples = tests más simples

## 📝 Hooks Disponibles

### `useInstances()`
Maneja la lista de instancias y su actualización automática.

```javascript
const { instanceList, loading, fetchInstances } = useInstances();
```

**Retorna:**
- `instanceList`: Array de instancias
- `loading`: Boolean de carga
- `fetchInstances`: Función para refrescar manualmente

---

### `useCreationLog()`
Maneja el polling del log de creación de instancias.

```javascript
const { creationLog, creationLogRef, startPolling, closeLog } = useCreationLog();
```

**Retorna:**
- `creationLog`: Estado del log { show, instanceName, log }
- `creationLogRef`: Ref para auto-scroll
- `startPolling(instanceName, isProduction)`: Iniciar polling
- `closeLog()`: Cerrar modal y detener polling

---

### `useUpdateLog()`
Maneja el polling del log de actualización de instancias.

```javascript
const { updateLog, updateLogRef, startPolling, closeLog } = useUpdateLog();
```

**Retorna:**
- `updateLog`: Estado del log { show, instanceName, action, log, completed }
- `updateLogRef`: Ref para auto-scroll
- `startPolling(instanceName, action)`: Iniciar polling
- `closeLog()`: Cerrar modal

---

### `useInstanceActions(fetchInstances, showToast, startUpdateLog)`
Maneja todas las acciones de instancias (start, stop, restart, update, etc.).

```javascript
const { actionLoading, handleAction } = useInstanceActions(
  fetchInstances,
  showToast,
  startUpdateLog
);
```

**Parámetros:**
- `fetchInstances`: Función para refrescar lista
- `showToast`: Función para mostrar notificaciones
- `startUpdateLog`: Función para iniciar polling de log de actualización

**Retorna:**
- `actionLoading`: Objeto con estado de carga por acción
- `handleAction(action, instanceName, options)`: Ejecutar acción

**Acciones soportadas:**
- `start`, `stop`, `restart`, `delete`
- `update-db`, `update-files`, `sync-filestore`, `regenerate-assets`

## 🔄 Migración Gradual

La refactorización puede hacerse gradualmente:

1. ✅ **Fase 1**: Crear hooks (COMPLETADO)
   - `useInstances`
   - `useCreationLog`
   - `useUpdateLog`
   - `useInstanceActions`

2. ✅ **Fase 2**: Crear modales básicos (COMPLETADO)
   - `CreationLogModal`
   - `UpdateLogModal`

3. 🔄 **Fase 3**: Crear modales de creación (PENDIENTE)
   - `CreateDevModal`
   - `CreateProdModal`

4. 🔄 **Fase 4**: Crear componentes de tarjetas (PENDIENTE)
   - `InstanceCard`
   - `InstanceActions`

5. 🔄 **Fase 5**: Refactorizar componente principal (PENDIENTE)
   - Usar hooks en lugar de lógica inline
   - Usar modales en lugar de JSX inline
   - Reducir de 1276 líneas a ~300 líneas

## 💡 Ejemplo de Uso

```javascript
import { useInstances, useCreationLog, useInstanceActions } from './instances/hooks';
import { CreationLogModal, UpdateLogModal } from './instances/modals';

export default function Instances() {
  // Hooks
  const { instanceList, loading, fetchInstances } = useInstances();
  const { creationLog, creationLogRef, startPolling, closeLog } = useCreationLog();
  const { actionLoading, handleAction } = useInstanceActions(
    fetchInstances,
    showToast,
    startUpdateLog
  );

  // Renderizado simplificado
  return (
    <div>
      {/* Lista de instancias */}
      {instanceList.map(instance => (
        <InstanceCard 
          key={instance.name}
          instance={instance}
          onAction={handleAction}
        />
      ))}

      {/* Modales */}
      <CreationLogModal 
        creationLog={creationLog}
        creationLogRef={creationLogRef}
        onClose={closeLog}
      />
    </div>
  );
}
```

## 🚀 Próximos Pasos

1. Completar modales de creación (CreateDevModal, CreateProdModal)
2. Extraer InstanceCard a componente separado
3. Refactorizar Instances.jsx para usar los nuevos módulos
4. Agregar tests unitarios para cada hook
5. Documentar props de cada componente

## 📚 Recursos

- [React Hooks](https://react.dev/reference/react)
- [Custom Hooks Best Practices](https://react.dev/learn/reusing-logic-with-custom-hooks)
- [Component Composition](https://react.dev/learn/passing-props-to-a-component)
