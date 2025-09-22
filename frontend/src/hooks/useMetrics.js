import { useEffect, useState } from 'react';
import axios from 'axios';
import { getMonth, getYear } from 'date-fns';
import { useFilters } from './useFilters';

export function useMetrics() {
  const { from, version } = useFilters();
  const [loading, setLoading] = useState(true);
  const [resumen, setResumen] = useState(null);
  const [rentabilidad, setRentabilidad] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const params = { mes: getMonth(from) + 1, anio: getYear(from) };
        const [r1, r2] = await Promise.all([
          axios.get('http://localhost:8000/api/reportes/resumen-mensual', { params }),
          axios.get('http://localhost:8000/api/reportes/rentabilidad', { params }),
        ]);
        setResumen(r1.data);
        setRentabilidad(r2.data);
        setRefreshKey(k => k + 1);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [from, version]);

  return { loading, resumen, rentabilidad, refreshKey };
}
export default useMetrics;


