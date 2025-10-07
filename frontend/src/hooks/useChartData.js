import { useEffect, useState } from 'react';
import axios from 'axios';
import { formatISO } from 'date-fns';
import { useFilters } from './useFilters';

export function useChartData() {
  const { from, to, localidad, version } = useFilters();
  const [loading, setLoading] = useState(true);
  const [operaciones, setOperaciones] = useState([]);

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setLoading(true);
        const params = {
          fecha_desde: formatISO(from, { representation: 'date' }),
          fecha_hasta: formatISO(to, { representation: 'date' }),
          localidad: localidad === 'Todas' ? undefined : localidad
        };
        const { data } = await axios.get('http://localhost:8000/api/reportes/operaciones-grafico', { params });
        setOperaciones(data.operaciones || []);
      } catch (error) {
        console.error('Error fetching chart data:', error);
        setOperaciones([]);
      } finally {
        setLoading(false);
      }
    };
    fetchChartData();
  }, [from, to, localidad, version]);

  return { operaciones, loading };
}

export default useChartData;

