import axios from 'axios';

// En producción, usar rutas relativas (mismo dominio)
// En desarrollo, usar localhost:5000
const API_URL = import.meta.env.MODE === 'production' 
  ? '' 
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000');

const api = axios.create({
  timeout: 0, // Sin timeout para uploads grandes
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
    api.get(`/api/instances/${name}`),
  
  create: (name) => 
    api.post('/api/instances/create', { name }),
  
  delete: (name) => 
    api.delete(`/api/instances/${name}`),
  
  updateDb: (name, neutralize = true) => 
    api.post(`/api/instances/${name}/update-db`, { neutralize }),
  
  updateFiles: (name) => 
    api.post(`/api/instances/${name}/update-files`),
  
  syncFilestore: (name) => 
    api.post(`/api/instances/${name}/sync-filestore`),
  
  regenerateAssets: (name) => 
    api.post(`/api/instances/${name}/regenerate-assets`),
  
  getLogs: (name, lines = 100, type = 'systemd') => 
    api.get(`/api/instances/${name}/logs?lines=${lines}&type=${type}`),
  
  restart: (name) => 
    api.post(`/api/instances/${name}/restart`),
  
  getCreationLog: (name) => 
    api.get(`/api/instances/creation-log/${name}`),
  
  getUpdateLog: (name, action) => 
    api.get(`/api/instances/update-log/${name}/${action}`),
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
};

export default api;
