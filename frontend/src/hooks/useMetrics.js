import { useEffect, useState } from 'react';
import axios from 'axios';
import { formatISO } from 'date-fns';
import { useFilters } from './useFilters';

export function useMetrics() {
  const { from, to, localidad, monedaVista, version } = useFilters();
  const [loading, setLoading] = useState(true);
  const [metricas, setMetricas] = useState(null);
  const [filtros, setFiltros] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const params = {
          fecha_desde: formatISO(from, { representation: 'date' }),
          fecha_hasta: formatISO(to, { representation: 'date' }),
          localidad: localidad === 'Todas' ? undefined : localidad,
          moneda_vista: monedaVista
        };
        const { data } = await axios.get('http://localhost:8000/api/reportes/dashboard', { params });
        setMetricas(data.metricas);
        setFiltros(data.filtros_aplicados);
        setRefreshKey(k => k + 1);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [from, to, localidad, monedaVista, version]);

  return { loading, metricas, filtros, refreshKey };
}
export default useMetrics;


