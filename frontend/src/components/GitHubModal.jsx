import { useState, useEffect } from 'react';
import { Github, CheckCircle, XCircle, Loader, AlertCircle, ChevronDown, ChevronUp, ExternalLink, RefreshCw, Trash2, Webhook, Copy, TestTube, GitBranch, Info, Terminal, Clock } from 'lucide-react';
import { github } from '../lib/api';

export default function GitHubModal({ isOpen, onClose, instanceName, onSuccess }) {
  const [step, setStep] = useState('input'); // input, verifying, configuring, success, error, git-actions, reconfigure, webhook
  const [githubToken, setGithubToken] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [githubUser, setGithubUser] = useState(null);
  const [existingConfig, setExistingConfig] = useState(null);
  const [commitMessage, setCommitMessage] = useState('');
  const [gitStatus, setGitStatus] = useState(null);
  const [gitLoading, setGitLoading] = useState(false);
  const [gitSuccess, setGitSuccess] = useState('');
  const [showInstructions, setShowInstructions] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // Branch selection states
  const [availableBranches, setAvailableBranches] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [showBranchSelector, setShowBranchSelector] = useState(false);
  const [branchesLoading, setBranchesLoading] = useState(false);
  const [showResetHardConfirm, setShowResetHardConfirm] = useState(false);
  const [resetHardBranch, setResetHardBranch] = useState('');
  
  // Webhook states
  const [showWebhookConfig, setShowWebhookConfig] = useState(false);
  const [webhookConfig, setWebhookConfig] = useState({
    auto_deploy: false,
    update_modules: false
  });
  const [webhookInfo, setWebhookInfo] = useState(null);
  const [copiedWebhook, setCopiedWebhook] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);

  // Deploy logs states
  const [showDeployLogs, setShowDeployLogs] = useState(false);
  const [deployLogs, setDeployLogs] = useState([]);
  const [deployLogsLoading, setDeployLogsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && instanceName) {
      checkExistingConfig();
    }
  }, [isOpen, instanceName]);

  const checkExistingConfig = async () => {
    try {
      const response = await github.getConfig(instanceName);
      if (response.data.success && response.data.config) {
        setExistingConfig(response.data.config);
        setStep('git-actions');
        loadGitStatus();
        // Load available branches for development instances
        if (instanceName.startsWith('dev-')) {
          loadAvailableBranches();
        }
      }
    } catch (error) {
      // No hay configuración existente, continuar normal
      setExistingConfig(null);
    }
  };

  const loadGitStatus = async () => {
    try {
      const response = await github.getStatus(instanceName);
      if (response.data.success) {
        setGitStatus(response.data);
      }
    } catch (error) {
      console.error('Error loading git status:', error);
    }
  };

  const loadAvailableBranches = async () => {
    setBranchesLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      console.log('Loading branches for:', instanceName);
      console.log('Token exists:', !!token);
      
      const response = await fetch(`/api/github/branches/${instanceName}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Branches response:', data);
      
      if (response.ok && data.success) {
        setAvailableBranches(data.branches || []);
        // Set default selected branch to current branch or main
        const currentBranch = data.current_branch;
        if (currentBranch && data.branches.includes(currentBranch)) {
          setSelectedBranch(currentBranch);
        } else if (data.branches.includes('main')) {
          setSelectedBranch('main');
        } else if (data.branches.length > 0) {
          setSelectedBranch(data.branches[0]);
        }
        
        // Show success message
        setGitSuccess(`✅ ${data.branches?.length || 0} ramas encontradas: ${data.branches?.join(', ') || 'ninguna'}`);
      } else {
        // Handle specific error cases
        if (response.status === 401) {
          setError('Error de autenticación. Por favor, verifica tu configuración de GitHub.');
        } else if (response.status === 404) {
          setError('Configuración de GitHub no encontrada para esta instancia.');
        } else {
          setError(`Error al cargar ramas: ${data.error || 'Error desconocido'}`);
        }
        
        // Set some default branches for testing
        setAvailableBranches(['main', 'develop', instanceName]);
        setSelectedBranch('main');
      }
    } catch (err) {
      console.error('Error loading branches:', err);
      setError(`Error de conexión: ${err.message}`);
      
      // Set some default branches for testing
      setAvailableBranches(['main', 'develop', instanceName]);
      setSelectedBranch('main');
    } finally {
      setBranchesLoading(false);
    }
  };

  const handleCommit = async () => {
    if (!commitMessage.trim()) {
      setError('Debes ingresar un mensaje de commit');
      return;
    }

    setGitLoading(true);
    setError('');
    setGitSuccess('');

    try {
      const response = await github.commit(instanceName, commitMessage);
      if (response.data.success) {
        setGitSuccess('Commit creado exitosamente');
        setCommitMessage('');
        loadGitStatus();
      } else {
        setError(response.data.error || 'Error al crear commit');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear commit');
    } finally {
      setGitLoading(false);
    }
  };

  const handlePush = async () => {
    setGitLoading(true);
    setError('');
    setGitSuccess('');

    try {
      const response = await github.push(instanceName);
      if (response.data.success) {
        setGitSuccess('Push realizado exitosamente');
        loadGitStatus();
      } else {
        setError(response.data.error || 'Error al hacer push');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al hacer push');
    } finally {
      setGitLoading(false);
    }
  };

  const handlePull = async (branchName = null, force = false, resetHard = false) => {
    setGitLoading(true);
    setError('');
    setGitSuccess('');

    try {
      const pullData = { instance_name: instanceName };
      if (branchName) {
        pullData.branch = branchName;
      }
      if (force) {
        pullData.force = true;
      }
      if (resetHard) {
        pullData.reset_hard = true;
      }
      
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/github/pull', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(pullData)
      });
      
      const data = await response.json();
      if (data.success) {
        const branch = branchName || existingConfig?.repo_branch || 'rama actual';
        let successMessage;
        if (resetHard) {
          successMessage = `🔄 Rama sobrescrita exitosamente con ${branch}`;
        } else {
          successMessage = `Pull realizado exitosamente desde ${branch}`;
        }
        if (data.warning) {
          successMessage += `\n⚠️ ${data.warning}`;
        }
        setGitSuccess(successMessage);
        loadGitStatus();
        // Recargar ramas para actualizar estado
        if (instanceName.startsWith('dev-')) {
          loadAvailableBranches();
        }
      } else {
        // Manejar errores específicos de seguridad
        if (data.suggested_action === 'commit_first') {
          setError(`${data.error}\n\n💡 ${data.warning}\n\nArchivos modificados: ${data.changes_info?.total || 0}`);
        } else {
          setError(data.error || 'Error al hacer pull');
        }
      }
    } catch (err) {
      setError(err.message || 'Error al hacer pull');
    } finally {
      setGitLoading(false);
    }
  };

  const parseRepoUrl = (url) => {
    // Soporta: https://github.com/owner/repo o github.com/owner/repo
    const match = url.match(/github\.com\/([^\/]+)\/([^\/\.]+)/);
    if (match) {
      return {
        owner: match[1],
        name: match[2]
      };
    }
    return null;
  };

  const handleConnect = async () => {
    // Limpiar espacios en blanco del token y URL
    const cleanToken = githubToken.trim();
    const cleanUrl = repoUrl.trim();
    
    if (!cleanToken || !cleanUrl) {
      setError('Debes completar todos los campos');
      return;
    }

    const repo = parseRepoUrl(cleanUrl);
    if (!repo) {
      setError('URL de repositorio inválida. Usa el formato: https://github.com/usuario/repositorio');
      return;
    }

    setLoading(true);
    setError('');
    setStep('verifying');

    try {
      // 1. Verificar token
      const verifyResponse = await github.verifyToken(cleanToken);
      if (!verifyResponse.data.success) {
        throw new Error('Token de GitHub inválido');
      }
      
      setGithubUser(verifyResponse.data);
      setStep('configuring');

      // 2. Crear configuración
      // Detectar si es producción o desarrollo
      const isProduction = !instanceName.startsWith('dev-');
      const basePath = isProduction ? '/home/mtg/apps/production/odoo' : '/home/mtg/apps/develop/odoo';
      const branch = isProduction ? 'main' : instanceName;
      
      const configData = {
        instance_name: instanceName,
        github_token: cleanToken,
        repo_owner: repo.owner,
        repo_name: repo.name,
        repo_branch: branch,
        local_path: `${basePath}/${instanceName}/custom_addons`
      };

      const configResponse = await github.createConfig(configData);
      if (!configResponse.data.success) {
        throw new Error('Error al crear la configuración');
      }

      // 3. Inicializar repositorio
      const initResponse = await github.initRepo(instanceName);
      if (!initResponse.data.success) {
        const errorMsg = initResponse.data.error || 'Error al inicializar el repositorio';
        throw new Error(errorMsg);
      }

      setStep('success');
      setTimeout(() => {
        onSuccess && onSuccess();
        handleClose();
      }, 2000);

    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Error al conectar con GitHub');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setLoading(true);
    setError('');
    setGitSuccess('');
    
    try {
      const response = await github.resetConfig(instanceName);
      if (response.data.success) {
        setGitSuccess('Configuración reseteada. Genera un nuevo token en GitHub.');
        setExistingConfig(null);
        setStep('reconfigure');
        setShowResetConfirm(false);
      } else {
        setError(response.data.error || 'Error al resetear configuración');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al resetear configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleResetHard = async (mode) => {
    setLoading(true);
    setError('');
    setGitSuccess('');
    
    try {
      const response = await github.resetHard(instanceName, mode);
      if (response.data.success) {
        const target = mode === 'main' ? 'main' : existingConfig?.repo_branch || 'rama actual';
        setGitSuccess(`Repositorio actualizado exitosamente desde ${target}`);
        // Recargar el estado de Git
        loadGitStatus();
      } else {
        setError(response.data.error || 'Error al actualizar repositorio');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al actualizar repositorio');
    } finally {
      setLoading(false);
    }
  };

  const handleReconfigure = async () => {
    const cleanToken = githubToken.trim();
    
    if (!cleanToken) {
      setError('Debes ingresar un token de GitHub');
      return;
    }

    setLoading(true);
    setError('');
    setStep('verifying');

    try {
      const response = await github.reconfigureConfig(instanceName, {
        github_token: cleanToken
      });
      
      if (response.data.success) {
        setGitSuccess('¡Configuración actualizada exitosamente!');
        setStep('success');
        setTimeout(() => {
          onSuccess && onSuccess();
          handleClose();
        }, 2000);
      } else {
        throw new Error(response.data.error || 'Error al reconfigurar');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Error al reconfigurar');
      setStep('reconfigure');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await github.deleteConfig(instanceName);
      if (response.data.success) {
        setGitSuccess('Configuración eliminada exitosamente');
        setExistingConfig(null);
        setShowDeleteConfirm(false);
        setTimeout(() => {
          onSuccess && onSuccess();
          handleClose();
        }, 1500);
      } else {
        setError(response.data.error || 'Error al eliminar configuración');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al eliminar configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setStep('input');
    setGithubToken('');
    setRepoUrl('');
    setError('');
    setGithubUser(null);
    setExistingConfig(null);
    setShowResetConfirm(false);
    setShowDeleteConfirm(false);
    setShowWebhookConfig(false);
    setWebhookInfo(null);
    onClose();
  };

  const handleConfigureWebhook = async () => {
    setLoading(true);
    setError('');
    setGitSuccess('');
    
    try {
      const response = await github.configureWebhook(instanceName, webhookConfig);
      if (response.data.success) {
        setWebhookInfo(response.data);
        setGitSuccess('Webhook configurado exitosamente');
        // Actualizar config existente
        setExistingConfig({
          ...existingConfig,
          auto_deploy: webhookConfig.auto_deploy,
          update_modules_on_deploy: webhookConfig.update_modules,
          has_webhook: true
        });
      } else {
        setError(response.data.error || 'Error al configurar webhook');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al configurar webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleTestWebhook = async () => {
    setGitLoading(true);
    setError('');
    setGitSuccess('');
    
    try {
      const response = await github.testWebhook(instanceName);
      if (response.data.success) {
        setGitSuccess('Test de webhook completado exitosamente');
        // Recargar estado
        loadGitStatus();
      } else {
        setError(response.data.error || 'Error en test de webhook');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error en test de webhook');
    } finally {
      setGitLoading(false);
    }
  };

  const loadDeployLogs = async () => {
    setDeployLogsLoading(true);
    try {
      const response = await github.getDeployLogs(instanceName, 50);
      if (response.data.success) {
        setDeployLogs(response.data.logs || []);
      }
    } catch (err) {
      console.error('Error loading deploy logs:', err);
    } finally {
      setDeployLogsLoading(false);
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'url') {
      setCopiedWebhook(true);
      setTimeout(() => setCopiedWebhook(false), 2000);
    } else {
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-gray-900 dark:bg-gray-700 p-2 rounded-lg">
            <Github className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {step === 'git-actions' ? 'Control de Versiones Git' : 
               step === 'reconfigure' ? 'Reconfigurar GitHub' : 
               'Conectar con GitHub'}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Instancia: {instanceName}
            </p>
          </div>
        </div>

        {/* Controles Git */}
        {step === 'git-actions' && existingConfig && (
          <div className="space-y-4">
            {/* Info del repositorio */}
            <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-3">
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-gray-700 dark:text-gray-300">
                  {existingConfig.repo_owner}/{existingConfig.repo_name} • {existingConfig.repo_branch}
                </span>
              </div>
            </div>

            {/* Estado del repositorio */}
            {gitStatus && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Estado del repositorio
                </p>
                {gitStatus.has_changes ? (
                  <div className="space-y-1">
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      {gitStatus.changes.length} archivo(s) modificado(s)
                    </p>
                    <div className="max-h-24 overflow-y-auto text-xs text-blue-600 dark:text-blue-400 space-y-0.5">
                      {gitStatus.changes.slice(0, 5).map((change, idx) => (
                        <div key={idx}>• {change.file}</div>
                      ))}
                      {gitStatus.changes.length > 5 && (
                        <div className="text-blue-500">... y {gitStatus.changes.length - 5} más</div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    No hay cambios pendientes
                  </p>
                )}
              </div>
            )}

            {/* Mensajes de éxito/error */}
            {gitSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                <p className="text-sm text-green-800 dark:text-green-200 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  {gitSuccess}
                </p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3">
                <p className="text-sm text-red-800 dark:text-red-200 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  {error}
                </p>
              </div>
            )}

            {/* Commit */}
            {gitStatus && gitStatus.has_changes && (
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Mensaje del commit
                </label>
                <input
                  type="text"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Descripción de los cambios..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 text-sm"
                  onKeyPress={(e) => e.key === 'Enter' && handleCommit()}
                />
                <button
                  onClick={handleCommit}
                  disabled={gitLoading || !commitMessage.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {gitLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Procesando...
                    </>
                  ) : (
                    'Commit (git add . && git commit)'
                  )}
                </button>
              </div>
            )}

            {/* Botones Push/Pull */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handlePush}
                disabled={gitLoading}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {gitLoading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  '↑ Push'
                )}
              </button>
              <button
                onClick={() => handlePull()}
                disabled={gitLoading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {gitLoading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : (
                  '↓ Pull'
                )}
              </button>
            </div>

            {/* Botones de gestión */}
            <div className="border-t border-gray-200 dark:border-gray-600 pt-4 mt-4 space-y-2">
              {/* Botón Webhook */}
              <button
                onClick={() => setShowWebhookConfig(!showWebhookConfig)}
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Webhook className="w-4 h-4" />
                {existingConfig?.has_webhook ? 'Configurar Webhook' : 'Habilitar Webhook'}
              </button>

              {/* Gestión de Ramas - Solo para desarrollo */}
              {instanceName.startsWith('dev-') && (
                <div className="space-y-2">
                  <button
                    onClick={() => {
                      setShowBranchSelector(!showBranchSelector);
                      if (!showBranchSelector && availableBranches.length === 0) {
                        loadAvailableBranches();
                      }
                    }}
                    disabled={loading}
                    className="w-full bg-gray-700 hover:bg-gray-600 text-white px-4 py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-between"
                  >
                    <span className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4" />
                      Gestión de Ramas
                    </span>
                    <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showBranchSelector ? 'rotate-180' : ''}`} />
                  </button>

                  {showBranchSelector && (
                    <div className="bg-gray-800/50 rounded-lg border border-gray-700 overflow-hidden">
                      {/* Selector de rama */}
                      <div className="p-3 border-b border-gray-700">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">Rama destino</span>
                          <button
                            onClick={loadAvailableBranches}
                            disabled={branchesLoading}
                            className="text-gray-400 hover:text-white transition-colors"
                            title="Recargar ramas del repositorio"
                          >
                            <RefreshCw className={`w-3 h-3 ${branchesLoading ? 'animate-spin' : ''}`} />
                          </button>
                        </div>
                        <select
                          value={selectedBranch}
                          onChange={(e) => setSelectedBranch(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-600 rounded-lg bg-gray-700 text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        >
                          {availableBranches.length > 0 ? (
                            availableBranches.map(branch => (
                              <option key={branch} value={branch}>{branch}</option>
                            ))
                          ) : (
                            <>
                              <option value="main">main</option>
                              <option value={instanceName}>{instanceName}</option>
                            </>
                          )}
                        </select>
                        {branchesLoading && (
                          <div className="text-xs text-blue-400 mt-1 flex items-center gap-1">
                            <Loader className="w-3 h-3 animate-spin" /> Cargando ramas...
                          </div>
                        )}
                      </div>

                      {/* Acciones */}
                      <div className="p-3 flex gap-2">
                        <button
                          onClick={() => handlePull(selectedBranch)}
                          disabled={gitLoading || !selectedBranch}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
                        >
                          Merge desde {selectedBranch ? selectedBranch.replace('origin/', '') : '...'}
                        </button>
                        <button
                          onClick={() => {
                            setResetHardBranch(selectedBranch || instanceName);
                            setShowResetHardConfirm(true);
                          }}
                          disabled={gitLoading || !selectedBranch}
                          className="bg-red-700/80 hover:bg-red-600 text-white px-3 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 border border-red-600/50"
                          title="Descarta TODOS tus cambios locales y deja tu código idéntico a la rama seleccionada"
                        >
                          Reset Hard
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              <button
                onClick={() => setShowResetConfirm(true)}
                disabled={loading}
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Resetear Configuración
              </button>
              <button
                onClick={() => setShowDeleteConfirm(true)}
                disabled={loading}
                className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Eliminar Configuración
              </button>
            </div>

            {/* Configuración de Webhook */}
            {showWebhookConfig && (
              <div className="border-t border-gray-200 dark:border-gray-600 pt-4 mt-4 space-y-4">
                <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-700 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-indigo-900 dark:text-indigo-100 mb-3 flex items-center gap-2">
                    <Webhook className="w-4 h-4" />
                    Configuración de Webhook
                  </h4>
                  
                  <div className="space-y-3">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={webhookConfig.auto_deploy}
                        onChange={(e) => setWebhookConfig({...webhookConfig, auto_deploy: e.target.checked})}
                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Auto-deploy en push a main
                      </span>
                    </label>
                    
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={webhookConfig.update_modules}
                        onChange={(e) => setWebhookConfig({...webhookConfig, update_modules: e.target.checked})}
                        className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        Actualizar módulos Odoo automáticamente
                      </span>
                    </label>
                  </div>

                  <button
                    onClick={handleConfigureWebhook}
                    disabled={loading}
                    className="w-full mt-3 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <Loader className="w-4 h-4 animate-spin" />
                        Configurando...
                      </>
                    ) : (
                      'Guardar Configuración'
                    )}
                  </button>

                  {/* Información del webhook */}
                  {webhookInfo && (
                    <div className="mt-4 space-y-3 pt-3 border-t border-indigo-200 dark:border-indigo-700">
                      <div>
                        <label className="block text-xs font-medium text-indigo-900 dark:text-indigo-100 mb-1">
                          URL del Webhook
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={webhookInfo.webhook_url}
                            readOnly
                            className="flex-1 px-3 py-2 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                          />
                          <button
                            onClick={() => copyToClipboard(webhookInfo.webhook_url, 'url')}
                            className="px-3 py-2 bg-indigo-100 dark:bg-indigo-900/50 hover:bg-indigo-200 dark:hover:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-lg transition-colors"
                          >
                            {copiedWebhook ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-indigo-900 dark:text-indigo-100 mb-1">
                          Secret
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="password"
                            value={webhookInfo.webhook_secret}
                            readOnly
                            className="flex-1 px-3 py-2 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white"
                          />
                          <button
                            onClick={() => copyToClipboard(webhookInfo.webhook_secret, 'secret')}
                            className="px-3 py-2 bg-indigo-100 dark:bg-indigo-900/50 hover:bg-indigo-200 dark:hover:bg-indigo-900 text-indigo-700 dark:text-indigo-300 rounded-lg transition-colors"
                          >
                            {copiedSecret ? <CheckCircle className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                        <p className="text-xs text-blue-800 dark:text-blue-200">
                          <strong>Próximo paso:</strong> Configura el webhook en GitHub → Settings → Webhooks → Add webhook
                        </p>
                      </div>

                      <button
                        onClick={handleTestWebhook}
                        disabled={gitLoading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {gitLoading ? (
                          <>
                            <Loader className="w-4 h-4 animate-spin" />
                            Probando...
                          </>
                        ) : (
                          <>
                            <TestTube className="w-4 h-4" />
                            Probar Webhook
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Historial de Deploy/Git */}
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
              <button
                onClick={() => {
                  setShowDeployLogs(!showDeployLogs);
                  if (!showDeployLogs && deployLogs.length === 0) loadDeployLogs();
                }}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Historial de Actividad Git
                  </span>
                </div>
                {showDeployLogs ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>

              {showDeployLogs && (
                <div className="bg-gray-950 border-t border-gray-700">
                  {/* Toolbar */}
                  <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800">
                    <span className="text-xs text-gray-500">{deployLogs.length} registros</span>
                    <button
                      onClick={loadDeployLogs}
                      disabled={deployLogsLoading}
                      className="text-gray-400 hover:text-white p-1 rounded transition-colors"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${deployLogsLoading ? 'animate-spin' : ''}`} />
                    </button>
                  </div>

                  {/* Log entries */}
                  <div className="max-h-64 overflow-y-auto font-mono text-xs">
                    {deployLogsLoading && deployLogs.length === 0 ? (
                      <div className="flex items-center justify-center py-8 text-gray-500">
                        <Loader className="w-4 h-4 animate-spin mr-2" />
                        Cargando...
                      </div>
                    ) : deployLogs.length === 0 ? (
                      <div className="text-center py-8 text-gray-600">
                        No hay registros de actividad
                      </div>
                    ) : (
                      deployLogs.map((log, idx) => {
                        const isError = log.status === 'error';
                        const isWebhook = log.action.includes('webhook');
                        const isPull = log.action.includes('pull');
                        const isPush = log.action.includes('push');
                        const isCommit = log.action.includes('commit');
                        const isReset = log.action.includes('reset');

                        const actionLabel = isWebhook ? 'WEBHOOK' :
                          isPull ? 'PULL' : isPush ? 'PUSH' :
                          isCommit ? 'COMMIT' : isReset ? 'RESET' : log.action.toUpperCase();

                        const actionColor = isError
                          ? 'bg-red-600 text-red-100'
                          : isWebhook ? 'bg-purple-600 text-purple-100'
                          : isPull ? 'bg-blue-600 text-blue-100'
                          : isPush ? 'bg-green-600 text-green-100'
                          : isCommit ? 'bg-cyan-600 text-cyan-100'
                          : isReset ? 'bg-orange-600 text-orange-100'
                          : 'bg-gray-600 text-gray-100';

                        const rowBg = isError ? 'bg-red-900/20' : 'bg-transparent';

                        return (
                          <div
                            key={log.id || idx}
                            className={`${rowBg} px-3 py-1.5 border-b border-gray-800/50 hover:bg-gray-800/50 flex items-start gap-2`}
                          >
                            <span className="text-gray-600 whitespace-nowrap flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(log.timestamp).toLocaleString('es-AR', {
                                day: '2-digit', month: '2-digit',
                                hour: '2-digit', minute: '2-digit'
                              })}
                            </span>
                            <span className={`${actionColor} px-1.5 py-0.5 rounded text-[10px] font-bold whitespace-nowrap`}>
                              {actionLabel}
                            </span>
                            <span className={`${isError ? 'text-red-300' : 'text-gray-300'} flex-1 break-all`}>
                              {log.details || 'Sin detalles'}
                            </span>
                            <span className="text-gray-600 whitespace-nowrap">
                              {log.user}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Botón Cerrar */}
            <button
              onClick={handleClose}
              className="w-full bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors mt-2"
            >
              Cerrar
            </button>
          </div>
        )}

        {/* Formulario de entrada */}
        {step === 'input' && (
          <div className="space-y-4">
            {/* Acordeón de instrucciones */}
            <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowInstructions(!showInstructions)}
                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center justify-between text-left"
              >
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  📖 ¿Cómo generar un token de GitHub?
                </span>
                {showInstructions ? (
                  <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
              </button>
              
              {showInstructions && (
                <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600">
                  <ol className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">1.</span>
                      <span>Ve a GitHub → <strong>Settings</strong> (tu perfil, arriba a la derecha)</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">2.</span>
                      <span>Scroll hasta el final → <strong>Developer settings</strong></span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">3.</span>
                      <span><strong>Personal access tokens</strong> → <strong>Tokens (classic)</strong></span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">4.</span>
                      <span><strong>Generate new token</strong> → <strong>Generate new token (classic)</strong></span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">5.</span>
                      <span>Dale un nombre (ej: "Odoo Dev Panel")</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">6.</span>
                      <span>Selecciona expiración (recomendado: 90 días o sin expiración)</span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">7.</span>
                      <div className="flex-1">
                        <div>Marca estos scopes:</div>
                        <ul className="ml-4 mt-1 space-y-1">
                          <li className="flex items-center gap-2">
                            <CheckCircle className="w-3 h-3 text-green-600 dark:text-green-400" />
                            <strong>repo</strong> (marca la casilla principal, incluye todas las sub-opciones)
                          </li>
                          <li className="flex items-center gap-2">
                            <CheckCircle className="w-3 h-3 text-green-600 dark:text-green-400" />
                            <strong>user:email</strong>
                          </li>
                        </ul>
                      </div>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">8.</span>
                      <span>Scroll hasta el final → <strong>Generate token</strong></span>
                    </li>
                    <li className="flex gap-2">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 min-w-[20px]">9.</span>
                      <span><strong className="text-red-600 dark:text-red-400">¡COPIA EL TOKEN INMEDIATAMENTE!</strong> (empieza con <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">ghp_</code>)</span>
                    </li>
                  </ol>
                  <a
                    href="https://github.com/settings/tokens/new"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Ir a crear token en GitHub
                  </a>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Token de GitHub
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                El token debe empezar con <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">ghp_</code>
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                URL del Repositorio
              </label>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/usuario/repositorio"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
              <p className="text-sm text-blue-800 dark:text-blue-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>
                  {instanceName.startsWith('dev-') ? (
                    <>Se creará automáticamente una rama llamada <strong>{instanceName}</strong> en tu repositorio y se conectará la carpeta custom_addons.</>
                  ) : (
                    <>Se conectará a la rama <strong>main</strong> de tu repositorio y se sincronizará con la carpeta custom_addons de producción.</>
                  )}
                </span>
              </p>
            </div>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3">
                <p className="text-sm text-red-800 dark:text-red-200 flex items-center gap-2">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleConnect}
                disabled={loading}
                className="flex-1 bg-gray-900 hover:bg-gray-800 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Conectando...
                  </>
                ) : (
                  <>
                    <Github className="w-4 h-4" />
                    Conectar
                  </>
                )}
              </button>
              <button
                onClick={handleClose}
                disabled={loading}
                className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Verificando token */}
        {step === 'verifying' && (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader className="w-12 h-12 text-blue-600 animate-spin mb-4" />
            <p className="text-gray-700 dark:text-gray-300 font-medium">Verificando token de GitHub...</p>
          </div>
        )}

        {/* Configurando */}
        {step === 'configuring' && (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader className="w-12 h-12 text-blue-600 animate-spin mb-4" />
            <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">Configurando repositorio...</p>
            {githubUser && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Usuario: {githubUser.username}
              </p>
            )}
          </div>
        )}

        {/* Éxito */}
        {step === 'success' && (
          <div className="flex flex-col items-center justify-center py-8">
            <div className="bg-green-100 dark:bg-green-900/30 rounded-full p-3 mb-4">
              <CheckCircle className="w-12 h-12 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-gray-900 dark:text-white font-semibold text-lg mb-2">
              ¡Conectado exitosamente!
            </p>
            <p className="text-gray-600 dark:text-gray-300 text-sm text-center">
              Tu repositorio está listo para usar con la rama <strong>{instanceName}</strong>
            </p>
          </div>
        )}

        {/* Error */}
        {step === 'error' && (
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center py-4">
              <div className="bg-red-100 dark:bg-red-900/30 rounded-full p-3 mb-4">
                <XCircle className="w-12 h-12 text-red-600 dark:text-red-400" />
              </div>
              <p className="text-gray-900 dark:text-white font-semibold text-lg mb-2">
                Error al conectar
              </p>
              <p className="text-gray-600 dark:text-gray-300 text-sm text-center">
                {error}
              </p>
            </div>
            <button
              onClick={() => setStep('input')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              Intentar de nuevo
            </button>
          </div>
        )}

        {/* Formulario de Reconfiguración */}
        {step === 'reconfigure' && (
          <div className="space-y-4">
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-3 mb-4">
              <p className="text-sm text-yellow-800 dark:text-yellow-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>
                  La configuración ha sido reseteada. Genera un nuevo token en GitHub y pégalo aquí para reconfigurar.
                </span>
              </p>
            </div>

            {gitSuccess && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
                <p className="text-sm text-green-800 dark:text-green-200 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  {gitSuccess}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nuevo Token de GitHub
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                El token debe empezar con <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">ghp_</code>
              </p>
            </div>

            <a
              href="https://github.com/settings/tokens/new"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              <ExternalLink className="w-4 h-4" />
              Ir a crear token en GitHub
            </a>

            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-3">
                <p className="text-sm text-red-800 dark:text-red-200 flex items-center gap-2">
                  <XCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleReconfigure}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Reconfigurando...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Reconfigurar
                  </>
                )}
              </button>
              <button
                onClick={handleClose}
                disabled={loading}
                className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Modal de confirmación de Reset */}
        {showResetConfirm && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-yellow-100 dark:bg-yellow-900/30 p-2 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                </div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                  ¿Resetear configuración?
                </h4>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                Esto limpiará el token actual. Deberás generar un nuevo token en GitHub y reconfigurarlo.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleReset}
                  disabled={loading}
                  className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Reseteando...' : 'Resetear'}
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  disabled={loading}
                  className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal de confirmación de Reset Hard */}
        {showResetHardConfirm && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-red-100 dark:bg-red-900/30 p-2 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                  ⚠️ RESET HARD - ¡PELIGRO!
                </h4>
              </div>
              <div className="space-y-3 mb-6">
                <p className="text-sm text-red-600 dark:text-red-400 font-medium">
                  🚨 ESTA ACCIÓN ES IRREVERSIBLE
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Vas a <strong>SOBRESCRIBIR COMPLETAMENTE</strong> tu rama actual con <strong>{resetHardBranch}</strong>.
                </p>
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded border border-red-200 dark:border-red-800">
                  <p className="text-sm text-red-800 dark:text-red-200 font-medium mb-2">
                    ❌ SE PERDERÁN PERMANENTEMENTE:
                  </p>
                  <ul className="text-xs text-red-700 dark:text-red-300 space-y-1">
                    <li>• Todos los cambios no commiteados</li>
                    <li>• Todos los commits locales no pusheados</li>
                    <li>• Todo el trabajo no guardado</li>
                  </ul>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Tu rama quedará <strong>exactamente igual</strong> a {resetHardBranch}. 
                  Solo usa esto si realmente quieres descartar todo tu trabajo local.
                </p>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-800">
                  <input
                    type="checkbox"
                    id="confirmReset"
                    className="rounded"
                    onChange={(e) => {
                      const button = document.getElementById('resetHardButton');
                      button.disabled = !e.target.checked;
                    }}
                  />
                  <label htmlFor="confirmReset" className="text-sm text-yellow-800 dark:text-yellow-200">
                    Entiendo que perderé TODOS mis cambios locales
                  </label>
                </div>
                
                <div className="flex gap-3">
                  <button
                    id="resetHardButton"
                    onClick={() => {
                      handlePull(resetHardBranch, false, true);
                      setShowResetHardConfirm(false);
                    }}
                    disabled={true}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {gitLoading ? 'Sobrescribiendo...' : '🔄 SOBRESCRIBIR RAMA'}
                  </button>
                  <button
                    onClick={() => {
                      setShowResetHardConfirm(false);
                      setResetHardBranch('');
                    }}
                    disabled={gitLoading}
                    className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal de confirmación de Delete */}
        {showDeleteConfirm && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-lg">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm mx-4">
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-red-100 dark:bg-red-900/30 p-2 rounded-lg">
                  <Trash2 className="w-6 h-6 text-red-600 dark:text-red-400" />
                </div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                  ¿Eliminar configuración?
                </h4>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                Esto eliminará completamente la configuración de GitHub para esta instancia. Esta acción no se puede deshacer.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleDelete}
                  disabled={loading}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Eliminando...' : 'Eliminar'}
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  disabled={loading}
                  className="flex-1 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
