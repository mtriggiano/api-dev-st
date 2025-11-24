import { useState, useEffect, useRef } from 'react';
import { instances } from '../../../lib/api';

/**
 * Hook para manejar el log de actualización de instancias con polling
 */
export function useUpdateLog() {
  const [updateLog, setUpdateLog] = useState({ 
    show: false, 
    instanceName: '', 
    action: '', 
    log: '', 
    completed: false 
  });
  const updateLogRef = useRef(null);

  // Auto-scroll cuando el log cambia
  useEffect(() => {
    if (updateLogRef.current) {
      updateLogRef.current.scrollTop = updateLogRef.current.scrollHeight;
    }
  }, [updateLog.log]);

  const startPolling = (instanceName, action) => {
    setUpdateLog({ show: true, instanceName, action, log: '', completed: false });

    const pollLog = async () => {
      try {
        const logResponse = await instances.getUpdateLog(instanceName, action);
        
        if (logResponse.data.exists) {
          setUpdateLog(prev => ({
            ...prev,
            log: logResponse.data.log,
            completed: logResponse.data.completed
          }));

          if (logResponse.data.completed) {
            // Detener polling cuando se complete
            return true;
          }
        }
        return false;
      } catch (error) {
        console.error('Error fetching update log:', error);
        return false;
      }
    };

    // Polling cada 2 segundos
    const interval = setInterval(async () => {
      const completed = await pollLog();
      if (completed) {
        clearInterval(interval);
      }
    }, 2000);

    // Cleanup
    return () => clearInterval(interval);
  };

  const closeLog = () => {
    setUpdateLog({ show: false, instanceName: '', action: '', log: '', completed: false });
  };

  return { updateLog, updateLogRef, startPolling, closeLog };
}
