import { useEffect, useState } from 'react';
import { KeyRound, Save, Shield, Trash2, UserCircle2 } from 'lucide-react';

const API_URL = import.meta.env.MODE === 'production'
  ? ''
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000');

function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

export default function MyAccount() {
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || '{}'));
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingSshKey, setSavingSshKey] = useState(false);
  const [revokingSshKey, setRevokingSshKey] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [sshPublicKey, setSshPublicKey] = useState('');

  const loadMe = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/api/auth/me`, { headers: getAuthHeaders() });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo cargar tu cuenta');
      }

      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));
      setFirstName(data.first_name || '');
      setLastName(data.last_name || '');
    } catch (err) {
      setError(err.message || 'Error cargando tu cuenta');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMe();
  }, []);

  const handleSaveProfile = async (event) => {
    event.preventDefault();

    if (!user?.id) return;

    if (newPassword && newPassword !== confirmPassword) {
      setError('La confirmacion de la contrasena no coincide');
      return;
    }

    const payload = {
      first_name: firstName,
      last_name: lastName,
    };

    if (newPassword) {
      payload.password = newPassword;
    }

    setSavingProfile(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/api/users/${user.id}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo actualizar tu cuenta');
      }

      setUser(data.user);
      localStorage.setItem('user', JSON.stringify(data.user));
      setSuccess(data.message || 'Cuenta actualizada correctamente');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.message || 'Error actualizando tu cuenta');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSaveSshKey = async () => {
    if (!user?.id) return;

    const key = sshPublicKey.trim();
    if (!key) {
      setError('Pega una clave publica SSH antes de guardar');
      return;
    }

    setSavingSshKey(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/api/users/${user.id}/ssh-key`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ public_key: key }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo guardar la clave SSH');
      }

      setSuccess(data.message || 'Clave SSH configurada correctamente');
      setSshPublicKey('');
    } catch (err) {
      setError(err.message || 'Error configurando clave SSH');
    } finally {
      setSavingSshKey(false);
    }
  };

  const handleRevokeSshKey = async () => {
    if (!user?.id) return;

    setRevokingSshKey(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch(`${API_URL}/api/users/${user.id}/ssh-key`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'No se pudo revocar la clave SSH');
      }

      setSuccess(data.message || 'Clave SSH revocada correctamente');
      setSshPublicKey('');
    } catch (err) {
      setError(err.message || 'Error revocando clave SSH');
    } finally {
      setRevokingSshKey(false);
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
    <div className="max-w-3xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Mi Cuenta</h2>
        <p className="text-gray-600 dark:text-gray-300 mt-1">Gestiona tu perfil, contrasena y acceso SSH.</p>
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}
      {success && <div className="rounded-lg border border-green-200 bg-green-50 text-green-700 px-4 py-3 text-sm">{success}</div>}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
        <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
          <UserCircle2 className="w-5 h-5 text-blue-600" /> Perfil
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2">
            <p className="text-gray-500 dark:text-gray-400">Usuario API-DEV</p>
            <p className="font-semibold text-gray-900 dark:text-white">{user.username}</p>
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2">
            <p className="text-gray-500 dark:text-gray-400">Rol</p>
            <p className="font-semibold text-gray-900 dark:text-white inline-flex items-center gap-1"><Shield className="w-4 h-4" /> {user.role}</p>
          </div>
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 md:col-span-2">
            <p className="text-gray-500 dark:text-gray-400">Usuario Linux ligado</p>
            <p className="font-semibold text-gray-900 dark:text-white">{user.system_username || `apidev_u${user.id}`}</p>
          </div>
        </div>

        <form onSubmit={handleSaveProfile} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Nombre"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <input
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Apellido"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Nueva contrasena (opcional)"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirmar nueva contrasena"
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />

          <button
            type="submit"
            disabled={savingProfile}
            className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg disabled:opacity-60 inline-flex items-center justify-center gap-2"
          >
            <Save className="w-4 h-4" />
            {savingProfile ? 'Guardando...' : 'Guardar perfil y contrasena'}
          </button>
        </form>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-3">
        <div className="flex items-center gap-2 text-gray-900 dark:text-white font-semibold">
          <KeyRound className="w-5 h-5 text-slate-700" /> Clave publica SSH
        </div>

        <p className="text-sm text-gray-600 dark:text-gray-300">
          Pega tu clave publica SSH para acceder con tu usuario Linux ligado y trabajar en tus instancias asignadas.
        </p>

        <textarea
          rows={4}
          value={sshPublicKey}
          onChange={(e) => setSshPublicKey(e.target.value)}
          placeholder="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... usuario@equipo"
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <button
            type="button"
            onClick={handleSaveSshKey}
            disabled={savingSshKey}
            className="bg-slate-700 hover:bg-slate-800 text-white py-2 rounded-lg disabled:opacity-60"
          >
            {savingSshKey ? 'Guardando clave...' : 'Guardar clave SSH'}
          </button>
          <button
            type="button"
            onClick={handleRevokeSshKey}
            disabled={revokingSshKey}
            className="bg-red-600 hover:bg-red-700 text-white py-2 rounded-lg disabled:opacity-60 inline-flex items-center justify-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            {revokingSshKey ? 'Revocando...' : 'Revocar clave SSH'}
          </button>
        </div>
      </div>
    </div>
  );
}
