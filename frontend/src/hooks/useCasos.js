import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export function useCasos() {
  const [casos, setCasos] = useState([]);
  const [casoActual, setCasoActual] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Lista casos con filtros opcionales
   */
  const fetchCasos = useCallback(async (filtros = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        estado: filtros.estado,
        prioridad: filtros.prioridad,
        limit: filtros.limit || 20,
        offset: filtros.offset || 0,
      };

      // Remover undefined values
      Object.keys(params).forEach(key => 
        params[key] === undefined && delete params[key]
      );

      const { data } = await axiosClient.get('/api/casos/', { params });
      setCasos(data.casos || []);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar casos';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando casos:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Crea un nuevo caso
   */
  const crearCaso = useCallback(async (casoData) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.post('/api/casos/', casoData);
      
      toast.success('Caso creado correctamente');
      
      // Refrescar lista
      await fetchCasos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al crear caso';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error creando caso:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchCasos]);

  /**
   * Actualiza un caso existente
   */
  const actualizarCaso = useCallback(async (id, casoData) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.put(`/api/casos/${id}`, casoData);
      
      toast.success('Caso actualizado correctamente');
      
      // Actualizar caso actual si es el mismo
      if (casoActual?.id === id) {
        setCasoActual(data);
      }
      
      // Refrescar lista
      await fetchCasos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al actualizar caso';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error actualizando caso:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [casoActual, fetchCasos]);

  /**
   * Elimina un caso (soft delete)
   */
  const eliminarCaso = useCallback(async (id) => {
    const confirmacion = window.confirm(
      '¿Estás seguro de eliminar este caso? Esta acción no se puede deshacer.'
    );
    
    if (!confirmacion) return null;

    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.delete(`/api/casos/${id}`);
      
      toast.success(data.mensaje || 'Caso eliminado correctamente');
      
      // Limpiar caso actual si es el eliminado
      if (casoActual?.id === id) {
        setCasoActual(null);
      }
      
      // Refrescar lista
      await fetchCasos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar caso';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error eliminando caso:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [casoActual, fetchCasos]);

  return {
    casos,
    casoActual,
    loading,
    error,
    fetchCasos,
    crearCaso,
    actualizarCaso,
    eliminarCaso,
    setCasoActual,
  };
}

export default useCasos;
