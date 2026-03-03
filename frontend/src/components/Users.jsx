import { useEffect, useMemo, useState } from 'react';
import { KeyRound, Plus, Save, Shield, User, Users as UsersIcon } from 'lucide-react';

const API_URL = import.meta.env.MODE === 'production'
  ? ''
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000');

const ROLES = [
  { value: 'admin', label: 'Administrador' },
  { value: 'developer', label: 'Developer' },
  { value: 'viewer', label: 'Viewer' },
];

const emptyCreateForm = {
  username: '',
  password: '',
  role: 'viewer',
  first_name: '',
  last_name: '',
  assigned_instances: [],
};

const emptyEditForm = {
  id: null,
  username: '',
  password: '',
  role: 'viewer',
  first_name: '',
  last_name: '',
  assigned_instances: [],
};

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

function normalizeInstances(value) {
  if (!Array.isArray(value)) return [];
  return Array.from(new Set(value.filter(Boolean)));
}

export default function Users() {
  const [users, setUsers] = useState([]);
  const [instances, setInstances] = useState([]);
  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [editForm, setEditForm] = useState(emptyEditForm);
  const [loading, setLoading] = useState(true);
  const [savingCreate, setSavingCreate] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const currentUser = useMemo(() => JSON.parse(localStorage.getItem('user') || '{}'), []);

  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      const [usersResponse, instancesResponse] = await Promise.all([
        fetch(`${API_URL}/api/users`, { headers: getAuthHeaders() }),
        fetch(`${API_URL}/api/users/available-instances`, { headers: getAuthHeaders() }),
      ]);

      const usersData = await usersResponse.json();
      const instancesData = await instancesResponse.json();

      if (!usersResponse.ok) {
        throw new Error(usersData.error || 'No se pudieron cargar los usuarios');
      }

      if (!instancesResponse.ok) {
        throw new Error(instancesData.error || 'No se pudieron cargar las instancias');
      }

      setUsers(usersData.users || []);
      setInstances(instancesData.instances || []);
    } catch (err) {
      setError(err.message || 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const toggleCreateInstance = (instanceName) => {
    setCreateForm((prev) => {
      const next = prev.assigned_instances.includes(instanceName)
        ? prev.assigned_instances.filter((name) => name !== instanceName)
        : [...prev.assigned_instances, instanceName];
      return { ...prev, assigned_instances: normalizeInstances(next) };
    });
  };

  const toggleEditInstance = (instanceName) => {
    setEditForm((prev) => {
      const next = prev.assigned_instances.includes(instanceName)
        ? prev.assigned_instances.filter((name) => name !== instanceName)
        : [...prev.assigned_instances, instanceName];
      return { ...prev, assigned_instances: normalizeInstances(next) };
    });
  };

  const handleCreateUser = async (event) => {
    event.preventDefault();
    setSavingCreate(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/api/users`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(createForm),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo crear el usuario');
      }

      setSuccess(data.message || 'Usuario creado correctamente');
      setCreateForm(emptyCreateForm);
      await loadData();
    } catch (err) {
      setError(err.message || 'Error al crear usuario');
    } finally {
      setSavingCreate(false);
    }
  };

  const openEdit = (user) => {
    setEditForm({
      id: user.id,
      username: user.username,
      password: '',
      role: user.role || 'viewer',
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      assigned_instances: normalizeInstances(user.assigned_instances || []),
    });
    setError('');
    setSuccess('');
  };

  const handleUpdateUser = async (event) => {
    event.preventDefault();
    if (!editForm.id) return;

    setSavingEdit(true);
    setError('');
    setSuccess('');

    const payload = {
      username: editForm.username,
      role: editForm.role,
      first_name: editForm.first_name,
      last_name: editForm.last_name,
      assigned_instances: editForm.assigned_instances,
    };

    if (editForm.password) {
      payload.password = editForm.password;
    }

    try {
      const response = await fetch(`${API_URL}/api/users/${editForm.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo actualizar el usuario');
      }

      if (currentUser?.id === editForm.id) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      setSuccess(data.message || 'Usuario actualizado correctamente');
      setEditForm(emptyEditForm);
      await loadData();
    } catch (err) {
      setError(err.message || 'Error al actualizar usuario');
    } finally {
      setSavingEdit(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Gestión de Usuarios</h2>
        <p className="text-gray-600 dark:text-gray-300 mt-1">Crear cuentas, asignar instancias y actualizar datos de perfil.</p>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}
      {success && <div className="rounded-lg border border-green-200 bg-green-50 text-green-700 px-4 py-3 text-sm">{success}</div>}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <form onSubmit={handleCreateUser} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
          <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
            <Plus className="w-5 h-5 text-blue-600" /> Crear nuevo usuario
          </div>

          <input value={createForm.username} onChange={(e) => setCreateForm((p) => ({ ...p, username: e.target.value }))} required placeholder="Usuario" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          <input type="password" value={createForm.password} onChange={(e) => setCreateForm((p) => ({ ...p, password: e.target.value }))} required placeholder="Contraseña" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />

          <div className="grid grid-cols-2 gap-3">
            <input value={createForm.first_name} onChange={(e) => setCreateForm((p) => ({ ...p, first_name: e.target.value }))} placeholder="Nombre" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
            <input value={createForm.last_name} onChange={(e) => setCreateForm((p) => ({ ...p, last_name: e.target.value }))} placeholder="Apellido" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
          </div>

          <select value={createForm.role} onChange={(e) => setCreateForm((p) => ({ ...p, role: e.target.value }))} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
            {ROLES.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
          </select>

          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Instancias asignadas</p>
            <div className="max-h-48 overflow-auto rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2">
              {instances.map((instance) => (
                <label key={instance.name} className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
                  <span>{instance.name} <span className="text-gray-400">({instance.type})</span></span>
                  <input type="checkbox" checked={createForm.assigned_instances.includes(instance.name)} onChange={() => toggleCreateInstance(instance.name)} />
                </label>
              ))}
            </div>
          </div>

          <button type="submit" disabled={savingCreate} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg disabled:opacity-60">
            {savingCreate ? 'Creando...' : 'Crear Usuario'}
          </button>
        </form>

        <form onSubmit={handleUpdateUser} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
          <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
            <Save className="w-5 h-5 text-green-600" /> Editar usuario
          </div>

          {!editForm.id && <p className="text-sm text-gray-500 dark:text-gray-400">Selecciona un usuario desde la lista para editarlo.</p>}

          <input value={editForm.username} onChange={(e) => setEditForm((p) => ({ ...p, username: e.target.value }))} disabled={!editForm.id} required placeholder="Usuario" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-60" />
          <input type="password" value={editForm.password} onChange={(e) => setEditForm((p) => ({ ...p, password: e.target.value }))} disabled={!editForm.id} placeholder="Nueva contraseña (opcional)" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-60" />

          <div className="grid grid-cols-2 gap-3">
            <input value={editForm.first_name} onChange={(e) => setEditForm((p) => ({ ...p, first_name: e.target.value }))} disabled={!editForm.id} placeholder="Nombre" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-60" />
            <input value={editForm.last_name} onChange={(e) => setEditForm((p) => ({ ...p, last_name: e.target.value }))} disabled={!editForm.id} placeholder="Apellido" className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-60" />
          </div>

          <select value={editForm.role} onChange={(e) => setEditForm((p) => ({ ...p, role: e.target.value }))} disabled={!editForm.id} className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-60">
            {ROLES.map((role) => <option key={role.value} value={role.value}>{role.label}</option>)}
          </select>

          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Instancias asignadas</p>
            <div className="max-h-48 overflow-auto rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2">
              {instances.map((instance) => (
                <label key={instance.name} className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
                  <span>{instance.name} <span className="text-gray-400">({instance.type})</span></span>
                  <input type="checkbox" disabled={!editForm.id} checked={editForm.assigned_instances.includes(instance.name)} onChange={() => toggleEditInstance(instance.name)} />
                </label>
              ))}
            </div>
          </div>

          <button type="submit" disabled={!editForm.id || savingEdit} className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg disabled:opacity-60">
            {savingEdit ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
          <UsersIcon className="w-5 h-5 text-blue-600" />
          <h3 className="font-semibold text-gray-900 dark:text-white">Usuarios existentes</h3>
        </div>
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {users.map((user) => (
            <button key={user.id} onClick={() => openEdit(user)} className="w-full text-left px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/30">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <User className="w-4 h-4" /> {user.username}
                    {currentUser?.id === user.id && <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700">Tu cuenta</span>}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{user.first_name || '-'} {user.last_name || ''}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Instancias: {(user.assigned_instances || []).join(', ') || 'Sin asignar'}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-700 dark:text-gray-200 inline-flex items-center gap-1"><Shield className="w-4 h-4" /> {user.role}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 inline-flex items-center gap-1"><KeyRound className="w-3 h-3" /> editar</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
