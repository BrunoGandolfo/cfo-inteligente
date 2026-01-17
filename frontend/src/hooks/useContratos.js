import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export function useContratos() {
  const [contratos, setContratos] = useState([]);
  const [contratoActual, setContratoActual] = useState(null);
  const [categorias, setCategorias] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);

  /**
   * Lista contratos con filtros opcionales
   */
  const fetchContratos = useCallback(async (filtros = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        categoria: filtros.categoria,
        q: filtros.q,
        activo: filtros.activo !== undefined ? Boolean(filtros.activo) : true,
        skip: filtros.skip || 0,
        limit: filtros.limit || 50,
      };

      // Remover undefined y null values
      Object.keys(params).forEach(key => 
        (params[key] === undefined || params[key] === null) && delete params[key]
      );

      const { data } = await axiosClient.get('/api/contratos/', { params });
      
      setContratos(data.contratos || []);
      setCategorias(data.categorias || []);
      setTotal(data.total || 0);
      
      return data;
    } catch (err) {
      // Manejar errores de validación de FastAPI (422)
      let errorMsg = 'Error al cargar contratos';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map(e => e.msg || e.message || String(e)).join(', ');
        } else {
          errorMsg = typeof err.response.data.detail === 'string' 
            ? err.response.data.detail 
            : err.response.data.detail?.message || String(err.response.data.detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando contratos:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtiene detalle de un contrato por ID
   */
  const fetchContrato = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get(`/api/contratos/${id}`);
      setContratoActual(data);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar contrato';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando contrato:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtiene lista de categorías únicas
   */
  const fetchCategorias = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get('/api/contratos/categorias');
      setCategorias(data || []);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar categorías';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando categorías:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Busca contratos por texto (full-text search)
   */
  const buscarContratos = useCallback(async (query, categoria = null) => {
    try {
      setLoading(true);
      setError(null);
      
      const params = {
        q: query,
        categoria: categoria,
        limit: 20,
      };

      // Remover null values
      Object.keys(params).forEach(key => 
        params[key] === null && delete params[key]
      );

      const { data } = await axiosClient.get('/api/contratos/buscar', { params });
      
      setContratos(data || []);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al buscar contratos';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error buscando contratos:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Descarga el archivo DOCX del contrato
   */
  const descargarContrato = useCallback(async (id, titulo = 'contrato') => {
    try {
      setError(null);
      
      const token = localStorage.getItem('token');
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://cfo-inteligente-production.up.railway.app';
      const url = `${API_BASE_URL}/api/contratos/${id}/descargar`;
      
      // Crear link temporal para descarga
      const link = document.createElement('a');
      link.href = url;
      link.download = `${titulo.replace(/\s+/g, '_')}.docx`;
      
      // Agregar token si existe (para endpoints protegidos, aunque este es público)
      if (token) {
        // Usar fetch para descarga con headers
        const response = await fetch(url, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('Error al descargar contrato');
        }
        
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        link.href = blobUrl;
      }
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Limpiar blob URL después de un momento
      if (token) {
        setTimeout(() => window.URL.revokeObjectURL(link.href), 100);
      }
      
      toast.success('Descarga iniciada');
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al descargar contrato';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error descargando contrato:', err);
      return false;
    }
  }, []);

  /**
   * Crea un nuevo contrato (solo socios)
   */
  const crearContrato = useCallback(async (contratoData) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.post('/api/contratos/', contratoData);
      
      toast.success('Contrato creado correctamente');
      
      // Refrescar lista
      await fetchContratos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al crear contrato';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error creando contrato:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchContratos]);

  /**
   * Actualiza un contrato existente (solo socios)
   */
  const actualizarContrato = useCallback(async (id, contratoData) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.patch(`/api/contratos/${id}`, contratoData);
      
      toast.success('Contrato actualizado correctamente');
      
      // Actualizar contrato actual si es el mismo
      if (contratoActual?.id === id) {
        setContratoActual(data);
      }
      
      // Refrescar lista
      await fetchContratos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al actualizar contrato';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error actualizando contrato:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [contratoActual, fetchContratos]);

  /**
   * Elimina un contrato (soft delete, solo socios)
   */
  const eliminarContrato = useCallback(async (id) => {
    const confirmacion = window.confirm(
      '¿Estás seguro de eliminar este contrato? Esta acción no se puede deshacer.'
    );
    
    if (!confirmacion) return null;

    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.delete(`/api/contratos/${id}`);
      
      toast.success(data.message || 'Contrato eliminado correctamente');
      
      // Limpiar contrato actual si es el eliminado
      if (contratoActual?.id === id) {
        setContratoActual(null);
      }
      
      // Refrescar lista
      await fetchContratos();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar contrato';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error eliminando contrato:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [contratoActual, fetchContratos]);

  return {
    contratos,
    contratoActual,
    categorias,
    loading,
    error,
    total,
    fetchContratos,
    fetchContrato,
    fetchCategorias,
    buscarContratos,
    descargarContrato,
    crearContrato,
    actualizarContrato,
    eliminarContrato,
    setContratoActual,
  };
}

export default useContratos;
