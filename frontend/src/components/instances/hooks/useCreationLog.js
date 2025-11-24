import { useState, useEffect, useRef } from 'react';
import { instances } from '../../../lib/api';

/**
 * Hook para manejar el log de creación de instancias con polling
 */
export function useCreationLog() {
  const [creationLog, setCreationLog] = useState({ show: false, instanceName: '', log: '' });
  const creationLogRef = useRef(null);

  // Auto-scroll cuando el log cambia
  useEffect(() => {
    if (creationLogRef.current) {
      creationLogRef.current.scrollTop = creationLogRef.current.scrollHeight;
    }
  }, [creationLog.log]);

  // Cleanup polling interval cuando el componente se desmonta
  useEffect(() => {
    return () => {
      if (window._pollingInterval) {
        clearInterval(window._pollingInterval);
        window._pollingInterval = null;
      }
    };
  }, []);

  const startPolling = (instanceName, isProduction = false) => {
    setCreationLog({ 
      show: true, 
      instanceName, 
      log: isProduction ? 'Iniciando creación de instancia de producción...\n' : 'Iniciando creación...\n' 
    });

    // Limpiar polling anterior si existe
    if (window._pollingInterval) clearInterval(window._pollingInterval);

    // Intervalo de polling (3s para producción, 2s para dev)
    const interval = isProduction ? 3000 : 2000;
    
    window._pollingInterval = setInterval(async () => {
      try {
        const logResponse = await instances.getCreationLog(instanceName);
        setCreationLog(prev => ({
          ...prev,
          log: logResponse.data.log || "Log no disponible aún..."
        }));

        // Detectar finalización
        const finishMessages = [
          '✅ Instancia de desarrollo creada con éxito',
          '✅ ¡INSTANCIA CREADA EXITOSAMENTE!',
          'Instancia creada con éxito'
        ];

        if (logResponse.data.log && finishMessages.some(msg => logResponse.data.log.includes(msg))) {
          clearInterval(window._pollingInterval);
          window._pollingInterval = null;
        }
      } catch (error) {
        console.error('Error fetching creation log:', error);
      }
    }, interval);
  };

  const closeLog = () => {
    if (window._pollingInterval) {
      clearInterval(window._pollingInterval);
      window._pollingInterval = null;
    }
    setCreationLog({ show: false, instanceName: '', log: '' });
  };

  return { creationLog, creationLogRef, startPolling, closeLog };
}
