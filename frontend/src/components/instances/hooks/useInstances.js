import { useState, useEffect } from 'react';
import { instances } from '../../../lib/api';

/**
 * Hook para manejar la lista de instancias y su actualización
 */
export function useInstances() {
  const [instanceList, setInstanceList] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchInstances = async () => {
    try {
      const response = await instances.list();
      setInstanceList(response.data.instances);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching instances:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstances();
    const interval = setInterval(fetchInstances, 10000); // Actualizar cada 10 segundos
    return () => clearInterval(interval);
  }, []);

  return { instanceList, loading, fetchInstances };
}
