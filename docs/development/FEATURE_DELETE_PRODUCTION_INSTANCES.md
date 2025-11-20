# ✅ Nueva Funcionalidad: Eliminar Instancias de Producción

## 🎯 Objetivo

Implementar un botón para eliminar instancias de producción desde el panel web con **doble verificación** para evitar eliminaciones accidentales.

## 🔒 Seguridad: Doble Confirmación

### Paso 1: Advertencia Inicial
- Modal con advertencia clara sobre la irreversibilidad
- Lista de lo que se eliminará:
  - Base de datos completa
  - Todos los archivos y código
  - Filestore (imágenes, PDFs, etc.)
  - Configuración de Nginx
  - Servicio systemd
- Botones: "Cancelar" o "Continuar"

### Paso 2: Confirmación Escrita
- Usuario debe escribir exactamente: `BORRAR{nombre-instancia}`
- Ejemplo: `BORRARcliente1`
- El botón "Eliminar Definitivamente" solo se habilita si la confirmación es exacta
- Validación en frontend y backend

## 📁 Archivos Modificados

### 1. Backend - Service Manager

**Archivo**: `/home/mtg/api-dev/backend/services/instance_manager.py`

**Método agregado**: `delete_production_instance(instance_name, confirmation)`

```python
def delete_production_instance(self, instance_name, confirmation):
    """Elimina una instancia de producción con doble confirmación"""
    # Validar confirmación
    expected_confirmation = f"BORRAR{instance_name}"
    if confirmation != expected_confirmation:
        return {'success': False, 'error': f'Confirmación incorrecta...'}
    
    # Ejecutar script de eliminación
    script_path = os.path.join(self.scripts_path, 'odoo/remove-production.sh')
    process = subprocess.Popen(
        ['/bin/bash', script_path],
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Enviar nombre y confirmación al script
    process.stdin.write(f"{instance_name}\n{expected_confirmation}\n")
    process.stdin.close()
    
    process.wait(timeout=300)  # Timeout de 5 minutos
```

### 2. Backend - Routes

**Archivo**: `/home/mtg/api-dev/backend/routes/instances.py`

**Ruta agregada**: `DELETE /api/instances/production/<instance_name>`

```python
@instances_bp.route('/production/<instance_name>', methods=['DELETE'])
@jwt_required()
def delete_production_instance(instance_name):
    """Elimina una instancia de producción con doble confirmación"""
    # Solo administradores
    if user.role != 'admin':
        return jsonify({'error': 'Solo administradores...'}), 403
    
    # Obtener confirmación del request
    data = request.get_json() or {}
    confirmation = data.get('confirmation', '')
    
    if not confirmation:
        return jsonify({'error': 'Se requiere confirmación...'}), 400
    
    result = manager.delete_production_instance(instance_name, confirmation)
    
    # Log de la acción
    log_action(user_id, 'delete_production_instance', instance_name, ...)
```

**Permisos**: Solo usuarios con rol `admin` pueden eliminar instancias de producción.

### 3. Frontend - API Client

**Archivo**: `/home/mtg/api-dev/frontend/src/lib/api.js`

**Método agregado**:

```javascript
deleteProduction: (name, confirmation) => 
  api.delete(`/api/instances/production/${name}`, { 
    data: { confirmation } 
  })
```

### 4. Frontend - Component

**Archivo**: `/home/mtg/api-dev/frontend/src/components/Instances.jsx`

**Estado agregado**:

```javascript
const [deleteProductionModal, setDeleteProductionModal] = useState({ 
  show: false, 
  instanceName: '', 
  confirmation: '', 
  step: 1 
});
```

**Funciones agregadas**:

```javascript
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

  // Llamar a la API
  const response = await instances.deleteProduction(instanceName, confirmation);
  // ...
};
```

**Botón agregado en InstanceCard**:

```jsx
{isProduction && (
  <button
    onClick={() => onAction('delete-production', instance.name)}
    disabled={actionLoading[`delete-prod-${instance.name}`]}
    title="Eliminar permanentemente esta instancia de producción (requiere doble confirmación)"
    className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50 border border-red-300 dark:border-red-700"
  >
    <Trash2 className="w-4 h-4" />
    <span className="hidden sm:inline">Eliminar</span>
  </button>
)}
```

**Modal de doble confirmación**: Modal de 2 pasos con advertencias claras y validación estricta.

## 🎨 Interfaz de Usuario

### Botón de Eliminar

- **Ubicación**: Solo visible en instancias de producción
- **Color**: Rojo con borde para destacar peligrosidad
- **Icono**: Trash2 (papelera)
- **Texto**: "Eliminar"
- **Tooltip**: "Eliminar permanentemente esta instancia de producción (requiere doble confirmación)"

### Modal - Paso 1: Advertencia

```
┌─────────────────────────────────────────┐
│ 🔴 Eliminar Instancia de Producción    │
├─────────────────────────────────────────┤
│                                         │
│ ⚠️ ADVERTENCIA: Esta acción es         │
│    IRREVERSIBLE                         │
│                                         │
│ Estás a punto de eliminar la instancia │
│ de producción cliente1.                 │
│                                         │
│ Esto eliminará:                         │
│ • La base de datos completa             │
│ • Todos los archivos y código           │
│ • El filestore (imágenes, PDFs, etc.)   │
│ • La configuración de Nginx             │
│ • El servicio systemd                   │
│                                         │
│ [Cancelar]         [Continuar]          │
└─────────────────────────────────────────┘
```

### Modal - Paso 2: Confirmación Escrita

```
┌─────────────────────────────────────────┐
│ 🔴 Eliminar Instancia de Producción    │
├─────────────────────────────────────────┤
│                                         │
│ Para confirmar la eliminación,          │
│ escribe exactamente:                    │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ BORRARcliente1                      │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [Escribe aquí...]                   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Cancelar]  [Eliminar Definitivamente] │
│                      (deshabilitado)    │
└─────────────────────────────────────────┘
```

## 🔐 Validaciones de Seguridad

### Frontend
1. ✅ Modal de 2 pasos obligatorio
2. ✅ Confirmación escrita exacta
3. ✅ Botón deshabilitado hasta confirmación correcta
4. ✅ Solo visible para instancias de producción

### Backend
1. ✅ Solo usuarios con rol `admin`
2. ✅ Validación de confirmación en el servidor
3. ✅ Mensaje de error si confirmación incorrecta
4. ✅ Timeout de 5 minutos para el proceso
5. ✅ Log de la acción para auditoría

### Script
1. ✅ Confirmación requerida: `BORRAR{nombre}`
2. ✅ Validación estricta del nombre
3. ✅ Log de eliminación en `/var/log/odoo-instances-removal.log`

## 📊 Flujo Completo

```
Usuario clic en "Eliminar" (instancia de producción)
         ↓
Modal Paso 1: Advertencia
         ↓
Usuario clic en "Continuar"
         ↓
Modal Paso 2: Confirmación escrita
         ↓
Usuario escribe: BORRARcliente1
         ↓
Botón "Eliminar Definitivamente" se habilita
         ↓
Usuario clic en "Eliminar Definitivamente"
         ↓
Frontend valida confirmación
         ↓
POST a /api/instances/production/cliente1
  Body: { confirmation: "BORRARcliente1" }
         ↓
Backend valida:
  - Usuario es admin ✓
  - Confirmación correcta ✓
         ↓
Backend ejecuta remove-production.sh
  - Envía nombre y confirmación al script
         ↓
Script elimina:
  - Detiene servicio systemd
  - Elimina base de datos
  - Elimina directorio de archivos
  - Elimina configuración Nginx
  - Elimina servicio systemd
  - Libera puerto
  - Registra en log
         ↓
Backend retorna éxito
         ↓
Frontend muestra toast: "Instancia eliminada"
         ↓
Frontend actualiza lista de instancias
```

## 🧪 Pruebas

### Caso 1: Eliminación Exitosa

1. Login como admin
2. Ir a "Instancias"
3. En una instancia de producción, clic en "Eliminar"
4. Modal aparece con advertencia
5. Clic en "Continuar"
6. Escribir exactamente: `BORRAR{nombre}`
7. Botón se habilita
8. Clic en "Eliminar Definitivamente"
9. Toast muestra "Instancia eliminada"
10. Instancia desaparece de la lista

### Caso 2: Confirmación Incorrecta

1. Seguir pasos 1-6
2. Escribir algo diferente: `borrarcliente1` (minúsculas)
3. Botón permanece deshabilitado
4. Intentar enviar (no debería poder)

### Caso 3: Usuario No Admin

1. Login como developer o viewer
2. Ir a "Instancias"
3. Botón "Eliminar" NO aparece en instancias de producción

### Caso 4: Cancelación

1. Seguir pasos 1-4
2. Clic en "Cancelar"
3. Modal se cierra
4. Instancia NO se elimina

## 📝 Logs y Auditoría

### Log de Aplicación

```python
log_action(
    user_id,
    'delete_production_instance',
    instance_name,
    result.get('message') or result.get('error'),
    'success' if result['success'] else 'error'
)
```

### Log del Sistema

```bash
# /var/log/odoo-instances-removal.log
2025-11-19 14:20:15 - Instancia: cliente1 - Puerto: 8070 - Dominio: cliente1.softrigx.com - Eliminada OK
```

## 🎯 Resultado

- ✅ Botón de eliminar agregado para instancias de producción
- ✅ Modal de doble confirmación implementado
- ✅ Validación en frontend y backend
- ✅ Solo administradores pueden eliminar
- ✅ Confirmación escrita obligatoria
- ✅ Logs de auditoría
- ✅ Interfaz clara y segura

---

**Fecha**: 19 Nov 2025 14:25
**Estado**: ✅ IMPLEMENTADO
**Próximo paso**: Probar eliminación de instancia de producción desde el panel web
