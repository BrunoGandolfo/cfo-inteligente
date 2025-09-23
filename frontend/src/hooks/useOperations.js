import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { isAfter, isBefore, parseISO } from 'date-fns';
import { useFilters } from './useFilters';
import toast from 'react-hot-toast';

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
    const confirmacion = window.confirm('¿Estás seguro de anular esta operación? Esta acción no se puede deshacer.');
    if (!confirmacion) return;
    try {
      await axios.patch(`http://localhost:8000/api/operaciones/${id}/anular`);
      toast.success('Operación anulada correctamente');
      fetchOperaciones();
    } catch (error) {
      toast.error('Error al anular operación');
      console.error(error);
    }
  };

  useEffect(() => { fetchOperaciones(); }, [refreshKey, version]);

  return { operaciones: filtered, operacionesAll: operaciones, loading, anular, refetch: fetchOperaciones };
}
export default useOperations;


