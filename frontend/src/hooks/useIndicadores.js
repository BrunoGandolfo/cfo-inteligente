/**
 * Hook para obtener indicadores económicos de Uruguay.
 * 
 * Obtiene: UI, UR, IPC, BPC y cotizaciones (USD, EUR, BRL).
 * Sigue el patrón de useMetrics.js.
 */

import { useEffect, useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';

export function useIndicadores() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indicadores, setIndicadores] = useState(null);

  const fetchIndicadores = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const { data } = await axiosClient.get('/api/indicadores/todos');
      setIndicadores(data);
    } catch (err) {
      console.error('Error obteniendo indicadores:', err);
      setError(err.message || 'Error al cargar indicadores');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIndicadores();
  }, [fetchIndicadores]);

  const refetch = useCallback(() => {
    fetchIndicadores();
  }, [fetchIndicadores]);

  return { indicadores, loading, error, refetch };
}

export default useIndicadores;
