import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export function useExpedientes() {
  const [expedientes, setExpedientes] = useState([]);
  const [expedienteActual, setExpedienteActual] = useState(null);
  const [historiaActual, setHistoriaActual] = useState(null);
  const [loadingHistoria, setLoadingHistoria] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [resumen, setResumen] = useState(null);

  /**
   * Lista expedientes con filtros opcionales
   */
  const fetchExpedientes = useCallback(async (filtros = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        socio_id: filtros.socioId,
        area_id: filtros.areaId,
        anio: filtros.anio,
        limit: filtros.limit || 20,
        offset: filtros.offset || 0,
      };

      // Remover undefined values
      Object.keys(params).forEach(key => 
        params[key] === undefined && delete params[key]
      );

      const { data } = await axiosClient.get('/api/expedientes/', { params });
      setExpedientes(data.expedientes || []);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar expedientes';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando expedientes:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtiene detalle de un expediente con sus movimientos
   */
  const fetchExpediente = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get(`/api/expedientes/${id}`);
      setExpedienteActual(data);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar expediente';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando expediente:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Sincroniza un nuevo expediente desde el Poder Judicial
   */
  const sincronizarNuevo = useCallback(async (iue, clienteId = null, areaId = null, socioId = null) => {
    try {
      setLoading(true);
      setError(null);
      
      const payload = {
        iue,
        cliente_id: clienteId,
        area_id: areaId,
        socio_responsable_id: socioId,
      };

      // Remover null values
      Object.keys(payload).forEach(key => 
        payload[key] === null && delete payload[key]
      );

      const { data } = await axiosClient.post('/api/expedientes/sincronizar', payload);
      
      toast.success(data.mensaje || 'Expediente sincronizado correctamente');
      
      // Refrescar lista
      await fetchExpedientes();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al sincronizar expediente';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error sincronizando expediente:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchExpedientes]);

  /**
   * Re-sincroniza un expediente existente
   */
  const reSincronizar = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.post(`/api/expedientes/${id}/sincronizar`);
      
      toast.success(data.mensaje || 'Expediente actualizado correctamente');
      
      // Actualizar expediente actual si es el mismo
      if (expedienteActual?.id === id) {
        setExpedienteActual(data.expediente);
      }
      
      // Refrescar lista
      await fetchExpedientes();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al re-sincronizar expediente';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error re-sincronizando expediente:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [expedienteActual, fetchExpedientes]);

  /**
   * Elimina un expediente (soft delete)
   */
  const eliminarExpediente = useCallback(async (id) => {
    const confirmacion = window.confirm(
      '¿Estás seguro de eliminar este expediente? Esta acción no se puede deshacer.'
    );
    
    if (!confirmacion) return null;

    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.delete(`/api/expedientes/${id}`);
      
      toast.success(data.mensaje || 'Expediente eliminado correctamente');
      
      // Limpiar expediente actual si es el eliminado
      if (expedienteActual?.id === id) {
        setExpedienteActual(null);
      }
      
      // Refrescar lista
      await fetchExpedientes();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar expediente';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error eliminando expediente:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [expedienteActual, fetchExpedientes]);

  /**
   * Obtiene estadísticas de sincronización
   */
  const fetchResumen = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get('/api/expedientes/resumen-sincronizacion');
      setResumen(data);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar resumen';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando resumen:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtiene la historia inteligente del expediente
   */
  const fetchHistoria = useCallback(async (id) => {
    console.log('fetchHistoria llamado con id:', id);
    try {
      setLoadingHistoria(true);
      setHistoriaActual(null); // Limpiar historia anterior
      setError(null);
      
      console.log('Llamando a API historia...');
      const { data } = await axiosClient.get(`/api/expedientes/${id}/historia`);
      console.log('Historia recibida:', data);
      
      setHistoriaActual(data);
      return data;
    } catch (err) {
      console.error('Error completo historia:', err);
      console.error('Response data:', err.response?.data);
      const errorMsg = err.response?.data?.detail || err.message || 'Error al generar historia';
      setError(errorMsg);
      toast.error(errorMsg);
      return null;
    } finally {
      setLoadingHistoria(false);
    }
  }, []);

  return {
    expedientes,
    expedienteActual,
    historiaActual,
    loadingHistoria,
    loading,
    error,
    resumen,
    fetchExpedientes,
    fetchExpediente,
    sincronizarNuevo,
    reSincronizar,
    eliminarExpediente,
    fetchResumen,
    fetchHistoria,
    setHistoriaActual,
  };
}

export default useExpedientes;

