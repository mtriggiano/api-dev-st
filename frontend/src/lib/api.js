import axios from 'axios';

// En producción, usar rutas relativas (mismo dominio)
// En desarrollo, usar localhost:5000
const API_URL = import.meta.env.MODE === 'production' 
  ? '' 
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000');

const api = axios.create({
  timeout: 30000, // Timeout seguro para evitar requests colgados
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Solo redirigir si es 401 y NO es la ruta de login
    if (error.response?.status === 401 && !error.config.url.includes('/api/auth/login')) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const auth = {
  login: (username, password) => 
    api.post('/api/auth/login', { username, password }),
  
  logout: () => 
    api.post('/api/auth/logout'),
  
  getCurrentUser: () => 
    api.get('/api/auth/me'),
};

export const metrics = {
  getCurrent: () => 
    api.get('/api/metrics/current'),
  
  getHistory: (minutes = 60) => 
    api.get(`/api/metrics/history?minutes=${minutes}`),
};

export const instances = {
  list: () => 
    api.get('/api/instances'),
  
  get: (name) => 
    api.get(`/api/instances/${encodeURIComponent(name)}`),
  
  // Método actualizado: ahora acepta sourceInstance
  create: (name, sourceInstance = null, neutralize = true) => 
    api.post('/api/instances/create', { name, sourceInstance, neutralize }),
  
  // Nuevo método: obtener instancias de producción disponibles
  getProductionInstances: () => 
    api.get('/api/instances/production-instances'),
  
  createProduction: (name, version = '19', edition = 'enterprise', sslMethod = 'letsencrypt') =>
    api.post('/api/instances/create-production', { name, version, edition, ssl_method: sslMethod }),
  
  delete: (name) => 
    api.delete(`/api/instances/${encodeURIComponent(name)}`),
  
  deleteProduction: (name, confirmation) => 
    api.delete(`/api/instances/production/${encodeURIComponent(name)}`, { data: { confirmation } }),
  
  updateDb: (name, neutralize = true) => 
    api.post(`/api/instances/${encodeURIComponent(name)}/update-db`, { neutralize }),
  
  updateFiles: (name) => 
    api.post(`/api/instances/${encodeURIComponent(name)}/update-files`),
  
  syncFilestore: (name) => 
    api.post(`/api/instances/${encodeURIComponent(name)}/sync-filestore`),
  
  regenerateAssets: (name) => 
    api.post(`/api/instances/${encodeURIComponent(name)}/regenerate-assets`),
  
  getLogs: (name, lines = 100, type = 'systemd') => 
    api.get(`/api/instances/${encodeURIComponent(name)}/logs?lines=${lines}&type=${type}`),
  
  restart: (name) => 
    api.post(`/api/instances/${encodeURIComponent(name)}/restart`),
  
  getCreationLog: (name) => 
    api.get(`/api/instances/creation-log/${encodeURIComponent(name)}`),
  
  getUpdateLog: (name, action) => 
    api.get(`/api/instances/update-log/${encodeURIComponent(name)}/${encodeURIComponent(action)}`),
};

export const logs = {
  list: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return api.get(`/api/logs?${query}`);
  },
  
  getStats: (hours = 24) => 
    api.get(`/api/logs/stats?hours=${hours}`),
};

export const backup = {
  list: () => 
    api.get('/api/backup/list'),
  
  create: () => 
    api.post('/api/backup/create'),
  
  download: (filename) => 
    api.get(`/api/backup/download/${filename}`, { responseType: 'blob' }),
  
  delete: (filename) => 
    api.delete(`/api/backup/delete/${filename}`),
  
  getConfig: () => 
    api.get('/api/backup/config'),
  
  updateConfig: (config) => 
    api.put('/api/backup/config', config),
  
  getLog: () => 
    api.get('/api/backup/log'),
  
  restore: (filename) => 
    api.post('/api/backup/restore', { filename, confirmed: true }),
  
  getRestoreLog: () => 
    api.get('/api/backup/restore/log'),
  
  upload: (formData, onProgress) => {
    return api.post('/api/backup/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          onProgress(progressEvent);
        }
      },
    });
  },
  
  getCronStatus: () => 
    api.get('/api/backup/cron/status'),
  
  restartCron: () => 
    api.post('/api/backup/cron/restart'),
};

export const github = {
  verifyToken: (token) => 
    api.post('/api/github/verify-token', { token }),
  
  getConfig: (instanceName) => 
    api.get(`/api/github/config/${instanceName}`),
  
  createConfig: (config) => 
    api.post('/api/github/config', config),
  
  initRepo: (instanceName) => 
    api.post('/api/github/init-repo', { instance_name: instanceName }),
  
  getStatus: (instanceName) => 
    api.get(`/api/github/status/${instanceName}`),
  
  commit: (instanceName, message, authorName, authorEmail) => 
    api.post('/api/github/commit', { 
      instance_name: instanceName, 
      message, 
      author_name: authorName, 
      author_email: authorEmail 
    }),
  
  push: (instanceName) => 
    api.post('/api/github/push', { instance_name: instanceName }),
  
  pull: (instanceName) => 
    api.post('/api/github/pull', { instance_name: instanceName }),
  
  getHistory: (instanceName, limit = 10) => 
    api.get(`/api/github/history/${instanceName}?limit=${limit}`),
  
  getDiff: (instanceName) => 
    api.get(`/api/github/diff/${instanceName}`),
  
  resetConfig: (instanceName) => 
    api.post(`/api/github/config/${instanceName}/reset`),
  
  reconfigureConfig: (instanceName, data) => 
    api.post(`/api/github/config/${instanceName}/reconfigure`, data),
  
  deleteConfig: (instanceName) => 
    api.delete(`/api/github/config/${instanceName}`),
  
  // Webhook endpoints
  configureWebhook: (instanceName, config) => 
    api.post(`/api/github/webhook/config/${instanceName}`, config),
  
  testWebhook: (instanceName) => 
    api.post(`/api/github/webhook/test/${instanceName}`),
  
  // Nuevos endpoints
  getCurrentCommit: (instanceName) => 
    api.get(`/api/github/current-commit/${instanceName}`),
  
  getDeployLogs: (instanceName, limit = 50) => 
    api.get(`/api/github/deploy-logs/${instanceName}?limit=${limit}`),
};

export default api;

// API V2 para backups multi-instancia
export const backupV2 = {
  // Gestión de instancias
  listInstances: () => 
    api.get('/api/backup/v2/instances'),
  
  getInstanceConfig: (instanceName) => 
    api.get(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/config`),
  
  updateInstanceConfig: (instanceName, config) => 
    api.put(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/config`, config),
  
  toggleAutoBackup: (instanceName, enabled) => 
    api.post(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/toggle`, { enabled }),
  
  // Backups
  listBackups: (instanceName) => 
    api.get(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backups`),
  
  createBackup: (instanceName) => 
    api.post(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backup`),
  
  deleteBackup: (instanceName, filename) => 
    api.delete(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backups/${encodeURIComponent(filename)}`),
  
  downloadBackup: (instanceName, filename) => 
    api.get(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backups/${encodeURIComponent(filename)}/download`, {
      responseType: 'blob'
    }),
  
  restoreBackup: (instanceName, filename) => 
    api.post(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/restore`, { filename }),
  
  uploadBackup: (instanceName, formData, onProgress) => 
    api.post(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    }),
  
  // Logs
  getBackupLog: (instanceName) => 
    api.get(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/backup-log`),
  
  getRestoreLog: (instanceName) => 
    api.get(`/api/backup/v2/instances/${encodeURIComponent(instanceName)}/restore-log`),
  
  // Estadísticas
  getGlobalStats: () => 
    api.get('/api/backup/v2/stats'),
};
