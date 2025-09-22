import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { isAfter, isBefore, parseISO } from 'date-fns';
import { useFilters } from './useFilters';

export function useOperations(refreshKey) {
  const { from, to, localidad, version } = useFilters();
  const [operaciones, setOperaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOperaciones = async () => {
    try {
      setLoading(true);
      const { data } = await axios.get('http://localhost:8000/api/operaciones', { params: { limit: 50 } });
      setOperaciones(data || []);
    } finally {
      setLoading(false);
    }
  };

  const filtered = useMemo(() => {
    return (operaciones || []).filter(op => {
      const d = parseISO(op.fecha);
      const inRange = (isAfter(d, from) || d.getTime() === from.getTime()) && (isBefore(d, to) || d.getTime() === to.getTime());
      const locOk = localidad === 'Todas' || (op.localidad ? op.localidad === localidad : true);
      return inRange && locOk;
    });
  }, [operaciones, from, to, localidad]);

  const anular = async (id) => {
    if (!window.confirm('¿Anular esta operación?')) return;
    await axios.patch(`http://localhost:8000/api/operaciones/${id}/anular`);
    fetchOperaciones();
  };

  useEffect(() => { fetchOperaciones(); }, [refreshKey, version]);

  return { operaciones: filtered, loading, anular, refetch: fetchOperaciones };
}
export default useOperations;


