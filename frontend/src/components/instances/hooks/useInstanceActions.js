import { useState } from 'react';
import { instances } from '../../../lib/api';

/**
 * Hook para manejar acciones de instancias (start, stop, restart, delete, etc.)
 */
export function useInstanceActions(fetchInstances, showToast, startUpdateLog) {
  const [actionLoading, setActionLoading] = useState({});

  const handleAction = async (action, instanceName, options = {}) => {
    setActionLoading({ ...actionLoading, [`${action}-${instanceName}`]: true });
    
    try {
      let response;
      
      // Acciones que muestran log de actualización
      const logActions = ['update-db', 'update-files', 'sync-filestore', 'regenerate-assets'];
      
      if (logActions.includes(action)) {
        response = action === 'update-db' 
          ? await instances.updateDb(instanceName, options.neutralize ?? true)
          : action === 'update-files'
          ? await instances.updateFiles(instanceName)
          : action === 'sync-filestore'
          ? await instances.syncFilestore(instanceName)
          : await instances.regenerateAssets(instanceName);

        if (response.data.success) {
          startUpdateLog(instanceName, action);
        } else {
          showToast(response.data.error || 'Error en la operación', 'error');
        }
      } else {
        // Acciones simples
        response = action === 'start'
          ? await instances.start(instanceName)
          : action === 'stop'
          ? await instances.stop(instanceName)
          : action === 'restart'
          ? await instances.restart(instanceName)
          : action === 'delete'
          ? await instances.delete(instanceName)
          : null;

        if (response) {
          showToast(response.data.message || 'Operación exitosa', 'success');
          fetchInstances();
        }
      }
    } catch (error) {
      showToast(error.response?.data?.error || 'Error en la operación', 'error');
    } finally {
      setActionLoading({ ...actionLoading, [`${action}-${instanceName}`]: false });
    }
  };

  return { actionLoading, handleAction };
}
