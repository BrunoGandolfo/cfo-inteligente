import { useEffect, useMemo, useState } from 'react';
import axiosClient from '../services/api/axiosClient';
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
      const { data } = await axiosClient.get('/api/operaciones', { params: { limit: 50 } });
      setOperaciones(data || []);
    } finally {
      setLoading(false);
    }
  };

  const filtered = useMemo(() => {
    console.log('🔍 useOperations - Filtrado en cliente:');
    console.log('  Total operaciones (sin filtrar):', operaciones?.length || 0);
    console.log('  Filtros activos - from:', from, 'to:', to, 'localidad:', localidad);
    
    const result = (operaciones || []).filter(op => {
      const d = parseISO(op.fecha);
      const inRange = (isAfter(d, from) || d.getTime() === from.getTime()) && (isBefore(d, to) || d.getTime() === to.getTime());
      const locOk = localidad === 'Todas' || (op.localidad ? op.localidad === localidad : true);
      
      if (!inRange) {
        console.log(`    ❌ Excluida por fecha: ${op.fecha} (fuera de rango ${from.toISOString()} - ${to.toISOString()})`);
      }
      if (!locOk) {
        console.log(`    ❌ Excluida por localidad: ${op.localidad} (filtro: ${localidad})`);
      }
      
      return inRange && locOk;
    });
    
    console.log('  Resultado filtrado:', result.length, 'operaciones');
    console.log('  Primeras 3 filtradas:', result.slice(0, 3).map(op => ({ fecha: op.fecha, localidad: op.localidad })));
    console.log('');
    
    return result;
  }, [operaciones, from, to, localidad]);

  const anular = async (id) => {
    const confirmacion = window.confirm('¿Estás seguro de anular esta operación? Esta acción no se puede deshacer.');
    if (!confirmacion) return;
    try {
      await axiosClient.patch(`/api/operaciones/${id}/anular`);
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


