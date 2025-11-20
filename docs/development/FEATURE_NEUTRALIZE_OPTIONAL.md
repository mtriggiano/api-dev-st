# ✅ Feature: Neutralización Opcional en Instancias de Desarrollo

## 🎯 Objetivo

Permitir al usuario decidir si quiere neutralizar o no la base de datos al crear una instancia de desarrollo.

## 📋 Cambios Implementados

### 1. Script Bash: create-dev-instance.sh

**Líneas 68-69**: Agregado tercer parámetro opcional
```bash
# Obtener opción de neutralización (tercer argumento opcional: "neutralize" o "no-neutralize")
NEUTRALIZE_OPTION="${3:-neutralize}"
```

**Líneas 279-292**: Neutralización condicional
```bash
# Neutralizar base de datos (eliminar licencia, desactivar correos/crons)
if [[ "$NEUTRALIZE_OPTION" == "neutralize" ]]; then
  echo "🛡️  Neutralizando base de datos de desarrollo..."
  # Usar script SQL directo (no requiere importar Odoo)
  "$SCRIPTS_PATH/odoo/neutralize-database-sql.sh" "$DB_NAME"
  if [ $? -eq 0 ]; then
    echo "✅ Base de datos neutralizada correctamente"
  else
    echo "❌ Error al neutralizar base de datos"
    exit 1
  fi
else
  echo "⚠️  Neutralización omitida (base de datos sin modificar)"
fi
```

### 2. Backend: instance_manager.py

**Línea 170**: Agregado parámetro `neutralize`
```python
def create_dev_instance(self, name, source_instance=None, neutralize=True):
    """Crea una nueva instancia de desarrollo
    
    Args:
        name: Nombre de la instancia de desarrollo
        source_instance: Instancia de producción a clonar (opcional)
        neutralize: Si True, neutraliza la base de datos (elimina licencia, desactiva crons/correos)
    """
```

**Líneas 192-194**: Pasar parámetro al script
```python
# Agregar opción de neutralización como tercer argumento
neutralize_arg = 'neutralize' if neutralize else 'no-neutralize'
script_args.append(neutralize_arg)
```

### 3. Backend: routes/instances.py

**Líneas 75-76**: Obtener parámetro del request
```python
# Obtener opción de neutralización (por defecto True)
neutralize = data.get('neutralize', True)
```

**Línea 79**: Pasar parámetro al manager
```python
result = manager.create_dev_instance(data['name'], source_instance, neutralize)
```

**Líneas 82-83**: Logging mejorado
```python
source_msg = f" desde {source_instance}" if source_instance else ""
neutralize_msg = " (neutralizada)" if neutralize else " (sin neutralizar)"
```

### 4. Frontend: api.js

**Línea 72**: Agregado parámetro `neutralize`
```javascript
create: (name, sourceInstance = null, neutralize = true) => 
  api.post('/api/instances/create', { name, sourceInstance, neutralize }),
```

### 5. Frontend: Instances.jsx

**Línea 19**: Agregado estado
```javascript
const [neutralizeDatabase, setNeutralizeDatabase] = useState(true);
```

**Línea 165**: Pasar parámetro al API
```javascript
const response = await instances.create(newInstanceName, selectedSourceInstance, neutralizeDatabase);
```

**Líneas 422-441**: Checkbox en el modal
```jsx
{/* Checkbox de neutralización */}
<div className="mb-4">
  <label className="flex items-center gap-2 cursor-pointer">
    <input
      type="checkbox"
      checked={neutralizeDatabase}
      onChange={(e) => setNeutralizeDatabase(e.target.checked)}
      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
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
```

## 🎨 Interfaz de Usuario

### Modal de Creación

```
┌─────────────────────────────────────────┐
│ Crear Nueva Instancia de Desarrollo    │
├─────────────────────────────────────────┤
│                                         │
│ Clonar desde:                           │
│ [prod-panel3 ▼]                         │
│ Se clonará la base de datos y archivos │
│                                         │
│ Nombre:                                 │
│ [test1                               ]  │
│                                         │
│ ☑ Neutralizar base de datos            │
│   ✅ Se desactivarán crons, correos,   │
│   webhooks y se eliminará la licencia  │
│                                         │
│ ⚠️  La creación puede tardar varios    │
│     minutos. Se clonará desde          │
│     prod-panel3.                        │
│                                         │
│  [Crear]              [Cancelar]        │
└─────────────────────────────────────────┘
```

### Opciones del Checkbox

**Marcado (por defecto)**:
```
☑ Neutralizar base de datos
  ✅ Se desactivarán crons, correos, webhooks 
     y se eliminará la licencia Enterprise
```

**Desmarcado**:
```
☐ Neutralizar base de datos
  ⚠️  La instancia mantendrá todos los datos 
     y configuraciones de producción
```

## 📊 Flujo de Creación

### Con Neutralización (checkbox marcado)

```
Usuario marca checkbox ☑
         ↓
Frontend envía: { name: "test1", sourceInstance: "prod-panel3", neutralize: true }
         ↓
Backend ejecuta: ./create-dev-instance.sh test1 prod-panel3 neutralize
         ↓
Script ejecuta:
  ✅ Base de datos clonada
  ✅ Filestore copiado
  🛡️  Neutralizando base de datos...
  ✅ Neutralización completada
     - Crons desactivados
     - Correos desactivados
     - Webhooks desactivados
     - Licencia eliminada
  ✅ Instancia creada
```

### Sin Neutralización (checkbox desmarcado)

```
Usuario desmarca checkbox ☐
         ↓
Frontend envía: { name: "test1", sourceInstance: "prod-panel3", neutralize: false }
         ↓
Backend ejecuta: ./create-dev-instance.sh test1 prod-panel3 no-neutralize
         ↓
Script ejecuta:
  ✅ Base de datos clonada
  ✅ Filestore copiado
  ⚠️  Neutralización omitida (base de datos sin modificar)
  ✅ Instancia creada
```

## 🧪 Casos de Uso

### 1. Desarrollo Normal (con neutralización)
```
✅ Checkbox marcado
✅ Crons desactivados → No se ejecutan tareas automáticas
✅ Correos desactivados → No se envían emails
✅ Webhooks desactivados → No se hacen llamadas externas
✅ Licencia eliminada → No hay problemas de licencia Enterprise
```

### 2. Testing de Producción (sin neutralización)
```
☐ Checkbox desmarcado
⚠️  Crons activos → Se ejecutan tareas automáticas
⚠️  Correos activos → CUIDADO: Puede enviar emails
⚠️  Webhooks activos → CUIDADO: Puede hacer llamadas externas
⚠️  Licencia presente → Puede tener problemas de licencia
```

## ⚠️  Advertencias

### Sin Neutralización

**IMPORTANTE**: Si creas una instancia sin neutralizar:

1. **Correos**: La instancia puede enviar correos reales a clientes
2. **Webhooks**: Puede hacer llamadas a APIs externas
3. **Crons**: Se ejecutarán tareas automáticas (facturación, reportes, etc.)
4. **Licencia**: Puede tener conflictos con la licencia Enterprise

**Recomendación**: Solo desmarcar el checkbox si:
- Necesitas probar funcionalidades específicas de producción
- Sabes lo que estás haciendo
- Tienes control sobre los datos

## 📁 Archivos Modificados

```
/home/mtg/api-dev/
├── scripts/odoo/
│   └── create-dev-instance.sh          ← Parámetro neutralize opcional
├── backend/
│   ├── services/
│   │   └── instance_manager.py         ← Método con parámetro neutralize
│   └── routes/
│       └── instances.py                ← Ruta acepta neutralize
└── frontend/src/
    ├── lib/
    │   └── api.js                      ← API con parámetro neutralize
    └── components/
        └── Instances.jsx               ← Checkbox de neutralización
```

## 🎯 Resultado

- ✅ Usuario puede elegir si neutralizar o no
- ✅ Checkbox marcado por defecto (seguro)
- ✅ Descripción clara de cada opción
- ✅ Log muestra si se neutralizó o no
- ✅ Backend registra la opción en los logs

---

**Fecha**: 19 Nov 2025 09:20
**Estado**: ✅ IMPLEMENTADO Y COMPILADO
**Próximo paso**: Recarga el panel web y prueba crear una instancia con/sin neutralización
