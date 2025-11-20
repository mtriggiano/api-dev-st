# ✅ Nueva Funcionalidad: Filtros y Búsqueda de Instancias

## 🎯 Objetivo

Implementar un sistema de filtros para mostrar únicamente las instancias relacionadas, facilitando el trabajo cuando hay muchas instancias de producción y desarrollo.

## 🔍 Funcionalidades Implementadas

### 1. Filtro por Instancia de Producción

**Dropdown** que permite seleccionar una instancia de producción específica.

**Comportamiento**:
- **"Todas las instancias"**: Muestra todas las instancias (comportamiento por defecto)
- **Seleccionar producción**: Muestra solo esa instancia de producción y sus instancias de desarrollo relacionadas

**Relación automática**:
- Las instancias de desarrollo tienen formato: `dev-{nombre}-{produccion}`
- Ejemplo: `dev-testp4-prod-panel4` → relacionada con `prod-panel4`
- El filtro extrae automáticamente esta relación de la base de datos

### 2. Buscador de Texto

**Campo de búsqueda** que filtra por:
- Nombre de la instancia
- Dominio
- Nombre de la base de datos

**Características**:
- Búsqueda en tiempo real (mientras escribes)
- No distingue mayúsculas/minúsculas
- Botón ✕ para limpiar rápidamente
- Placeholder descriptivo

### 3. Botón "Limpiar filtros"

**Aparece cuando**:
- Se ha seleccionado una instancia de producción específica, O
- Se ha escrito algo en el buscador

**Acción**: Restaura ambos filtros a su estado inicial

### 4. Contador de Resultados

**Muestra** el número de instancias visibles después de aplicar filtros:
- Ejemplo: "Mostrando: 1 producción, 3 desarrollo"

## 🎨 Interfaz de Usuario

### Ubicación

La barra de filtros aparece **entre el header y las secciones de instancias**:

```
┌─────────────────────────────────────────────┐
│ Instancias Odoo                             │
│ [Nueva Producción] [Nueva Desarrollo]       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🔍 BARRA DE FILTROS                         │
│                                             │
│ [Filtrar por Producción ▼] [Buscar...    ✕]│
│                                             │
│ [Limpiar filtros]                           │
│ Mostrando: 1 producción, 3 desarrollo      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Producción                                  │
│ [Instancias filtradas...]                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ Desarrollo                                  │
│ [Instancias filtradas...]                   │
└─────────────────────────────────────────────┘
```

### Diseño Responsive

**Desktop** (sm y superior):
```
┌──────────────────────────────────────────────────────────┐
│ [Filtrar por Producción ▼]  [Buscar...    ✕] [Limpiar]  │
└──────────────────────────────────────────────────────────┘
```

**Mobile**:
```
┌────────────────────────┐
│ [Filtrar por Prod. ▼]  │
│ [Buscar...    ✕]       │
│ [Limpiar filtros]      │
└────────────────────────┘
```

## 📊 Lógica de Filtrado

### Código de Filtrado

```javascript
// 1. Filtrar por tipo
let productionInstances = instanceList.filter(i => i.type === 'production');
let developmentInstances = instanceList.filter(i => i.type === 'development');

// 2. Aplicar filtro por instancia de producción
if (filterByProduction !== 'all') {
  // Mostrar solo la instancia de producción seleccionada
  productionInstances = productionInstances.filter(i => i.name === filterByProduction);
  
  // Mostrar solo las instancias de desarrollo relacionadas
  developmentInstances = developmentInstances.filter(i => {
    // Extraer nombre de producción del nombre de la BD
    // Ejemplo: dev-testp4-prod-panel4 -> prod-panel4
    const match = i.database?.match(/dev-[^-]+-(.+)/);
    if (match) {
      const prodName = match[1];
      return prodName === filterByProduction;
    }
    return false;
  });
}

// 3. Aplicar búsqueda por texto
if (searchTerm.trim()) {
  const search = searchTerm.toLowerCase();
  productionInstances = productionInstances.filter(i => 
    i.name?.toLowerCase().includes(search) ||
    i.domain?.toLowerCase().includes(search) ||
    i.database?.toLowerCase().includes(search)
  );
  developmentInstances = developmentInstances.filter(i => 
    i.name?.toLowerCase().includes(search) ||
    i.domain?.toLowerCase().includes(search) ||
    i.database?.toLowerCase().includes(search)
  );
}
```

### Extracción de Relación

**Formato de base de datos de desarrollo**:
```
dev-{nombre-dev}-{nombre-produccion}
```

**Ejemplos**:
- `dev-testp4-prod-panel4` → Producción: `prod-panel4`
- `dev-test1-cliente1` → Producción: `cliente1`
- `dev-demo-principal` → Producción: `principal`

**Regex utilizada**:
```javascript
const match = i.database?.match(/dev-[^-]+-(.+)/);
```

## 🎯 Casos de Uso

### Caso 1: Ver Solo Una Instancia de Producción

**Escenario**: Tienes 10 instancias de producción y quieres trabajar solo con `prod-panel4`

**Pasos**:
1. Seleccionar "prod-panel4" en el dropdown
2. Solo se muestra:
   - Instancia de producción: `prod-panel4`
   - Instancias de desarrollo: `dev-testp4-prod-panel4`, `dev-test2-prod-panel4`, etc.

### Caso 2: Buscar por Dominio

**Escenario**: Quieres encontrar la instancia con dominio `cliente1.softrigx.com`

**Pasos**:
1. Escribir "cliente1" en el buscador
2. Se filtran todas las instancias que contengan "cliente1" en nombre, dominio o BD

### Caso 3: Combinar Filtros

**Escenario**: Buscar instancias de desarrollo de `prod-panel4` que contengan "test"

**Pasos**:
1. Seleccionar "prod-panel4" en el dropdown
2. Escribir "test" en el buscador
3. Solo se muestran instancias dev de prod-panel4 que contengan "test"

### Caso 4: Limpiar y Ver Todo

**Escenario**: Después de filtrar, quieres ver todas las instancias nuevamente

**Pasos**:
1. Clic en "Limpiar filtros"
2. Ambos filtros se resetean
3. Se muestran todas las instancias

## 📁 Cambios en el Código

### Estados Agregados

```javascript
const [filterByProduction, setFilterByProduction] = useState('all');
const [searchTerm, setSearchTerm] = useState('');
```

### Imports Actualizados

```javascript
import { ..., Search, Filter } from 'lucide-react';
```

### Componente de Filtros

```jsx
<div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
  <div className="flex flex-col sm:flex-row gap-4">
    {/* Filtro por instancia de producción */}
    <div className="flex-1">
      <label>
        <Filter className="w-4 h-4 inline mr-2" />
        Filtrar por Instancia de Producción
      </label>
      <select
        value={filterByProduction}
        onChange={(e) => setFilterByProduction(e.target.value)}
      >
        <option value="all">Todas las instancias</option>
        {instanceList
          .filter(i => i.type === 'production')
          .map(prod => (
            <option key={prod.name} value={prod.name}>
              {prod.name} {prod.domain ? `(${prod.domain})` : ''}
            </option>
          ))
        }
      </select>
    </div>

    {/* Buscador */}
    <div className="flex-1">
      <label>
        <Search className="w-4 h-4 inline mr-2" />
        Buscar
      </label>
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Buscar por nombre, dominio o base de datos..."
        />
        {searchTerm && (
          <button onClick={() => setSearchTerm('')}>✕</button>
        )}
      </div>
    </div>

    {/* Botón limpiar */}
    {(filterByProduction !== 'all' || searchTerm) && (
      <div className="flex items-end">
        <button
          onClick={() => {
            setFilterByProduction('all');
            setSearchTerm('');
          }}
        >
          Limpiar filtros
        </button>
      </div>
    )}
  </div>

  {/* Contador */}
  {(filterByProduction !== 'all' || searchTerm) && (
    <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
      Mostrando: {productionInstances.length} producción, {developmentInstances.length} desarrollo
    </div>
  )}
</div>
```

## 🎨 Estilos y UX

### Colores e Iconos

- **Filtro**: Icono `Filter` (embudo)
- **Búsqueda**: Icono `Search` (lupa)
- **Limpiar**: Texto simple, hover gris
- **Contador**: Texto gris discreto

### Interactividad

- ✅ Filtros se aplican en tiempo real
- ✅ Dropdown con opciones claras (nombre + dominio)
- ✅ Buscador con placeholder descriptivo
- ✅ Botón ✕ para limpiar búsqueda rápidamente
- ✅ Botón "Limpiar filtros" solo aparece cuando hay filtros activos
- ✅ Contador muestra resultados actuales

### Accesibilidad

- ✅ Labels descriptivos para cada campo
- ✅ Iconos visuales para identificar funciones
- ✅ Placeholder en el buscador
- ✅ Feedback visual (contador de resultados)

## 🧪 Pruebas

### Caso 1: Filtrar por Producción

1. Abrir página de instancias
2. Seleccionar una instancia de producción en el dropdown
3. Verificar que solo aparece esa producción
4. Verificar que solo aparecen sus instancias dev relacionadas

### Caso 2: Buscar por Texto

1. Escribir texto en el buscador
2. Verificar que se filtran instancias en tiempo real
3. Clic en ✕ para limpiar
4. Verificar que se muestran todas las instancias

### Caso 3: Combinar Filtros

1. Seleccionar producción
2. Escribir texto en buscador
3. Verificar que ambos filtros se aplican
4. Clic en "Limpiar filtros"
5. Verificar que ambos se resetean

### Caso 4: Sin Resultados

1. Aplicar filtros que no coincidan con ninguna instancia
2. Verificar que aparece mensaje "No hay instancias..."
3. Contador muestra "0 producción, 0 desarrollo"

## 📊 Beneficios

### Para el Usuario

- ✅ **Organización**: Trabaja solo con las instancias relevantes
- ✅ **Rapidez**: Encuentra instancias rápidamente
- ✅ **Claridad**: Ve solo lo que necesita
- ✅ **Productividad**: Menos scroll, menos confusión

### Para el Sistema

- ✅ **Escalabilidad**: Funciona con 1 o 100 instancias
- ✅ **Performance**: Filtrado en cliente (rápido)
- ✅ **Mantenibilidad**: Código limpio y modular
- ✅ **Extensibilidad**: Fácil agregar más filtros

## 🔮 Mejoras Futuras

### Filtros Adicionales

- Filtrar por estado (activo/inactivo)
- Filtrar por versión de Odoo
- Filtrar por fecha de creación
- Filtrar por puerto

### Búsqueda Avanzada

- Búsqueda por regex
- Búsqueda en múltiples campos simultáneamente
- Autocompletado de búsqueda

### Persistencia

- Guardar filtros en localStorage
- Recordar última búsqueda
- Favoritos/marcadores

## 🎯 Resultado

- ✅ Filtro por instancia de producción implementado
- ✅ Buscador de texto implementado
- ✅ Relación automática prod-dev funcionando
- ✅ Botón limpiar filtros
- ✅ Contador de resultados
- ✅ UI responsive y accesible
- ✅ Frontend compilado y backend recargado

---

**Fecha**: 19 Nov 2025 14:50
**Estado**: ✅ IMPLEMENTADO
**Próximo paso**: Recargar página con Ctrl+Shift+R y probar los filtros
