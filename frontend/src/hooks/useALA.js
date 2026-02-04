/**
 * Hook para módulo ALA (Anti-Lavado de Activos)
 * 
 * Maneja verificaciones de debida diligencia contra listas:
 * PEP (Uruguay), ONU, OFAC, UE, GAFI
 * 
 * Decreto 379/018 - Arts. 17-18, 44
 * 
 * @author Sistema CFO Inteligente
 * @date Febrero 2026
 */

import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export function useALA() {
  const [verificaciones, setVerificaciones] = useState([]);
  const [verificacionActual, setVerificacionActual] = useState(null);
  const [metadataListas, setMetadataListas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingBusquedas, setLoadingBusquedas] = useState(false);
  const [error, setError] = useState(null);
  const [totalVerificaciones, setTotalVerificaciones] = useState(0);

  /**
   * Ejecuta verificación completa ALA contra todas las listas
   * NOTA: Este endpoint tarda 20-60 segundos (descarga 4 listas externas)
   * 
   * @param {Object} datos - Datos de la persona a verificar
   * @param {string} datos.nombre_completo - Nombre completo (requerido)
   * @param {string} datos.tipo_documento - CI, RUT, PASAPORTE
   * @param {string} datos.numero_documento - Número de documento
   * @param {string} datos.nacionalidad - Código ISO (ej: UY, AR)
   * @param {string} datos.fecha_nacimiento - YYYY-MM-DD (opcional)
   * @param {boolean} datos.es_persona_juridica - Si es empresa
   * @param {string} datos.razon_social - Razón social si es PJ
   * @param {string} datos.expediente_id - UUID de expediente (opcional)
   * @param {string} datos.contrato_id - UUID de contrato (opcional)
   */
  const ejecutarVerificacion = useCallback(async (datos) => {
    try {
      setLoading(true);
      setError(null);
      setVerificacionActual(null);
      
      const { data } = await axiosClient.post('/api/ala/verificar', datos);
      
      setVerificacionActual(data);
      toast.success('Verificación ALA completada');
      
      return data;
    } catch (err) {
      let errorMsg = 'Error al ejecutar verificación ALA';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail.map(e => e.msg || String(e)).join(', ');
        } else {
          errorMsg = typeof err.response.data.detail === 'string' 
            ? err.response.data.detail 
            : String(err.response.data.detail);
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error ejecutando verificación ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Carga lista de verificaciones con paginación
   * 
   * @param {number} limit - Máximo de resultados (default 50, max 200)
   * @param {number} offset - Desplazamiento para paginación
   */
  const cargarVerificaciones = useCallback(async (limit = 50, offset = 0) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get('/api/ala/verificaciones', {
        params: { limit, offset }
      });
      
      setVerificaciones(data.verificaciones || []);
      setTotalVerificaciones(data.total || 0);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar verificaciones';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando verificaciones ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Obtiene una verificación por ID
   * 
   * @param {string} id - UUID de la verificación
   */
  const obtenerVerificacion = useCallback(async (id) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get(`/api/ala/verificaciones/${id}`);
      
      setVerificacionActual(data);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al obtener verificación';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error obteniendo verificación ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Actualiza campos Art. 44 C.4 de una verificación
   * 
   * @param {string} id - UUID de la verificación
   * @param {Object} datos - Campos a actualizar
   * @param {boolean} datos.busqueda_google_realizada
   * @param {string} datos.busqueda_google_observaciones
   * @param {boolean} datos.busqueda_news_realizada
   * @param {string} datos.busqueda_news_observaciones
   * @param {boolean} datos.busqueda_wikipedia_realizada
   * @param {string} datos.busqueda_wikipedia_observaciones
   */
  const actualizarVerificacion = useCallback(async (id, datos) => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.patch(`/api/ala/verificaciones/${id}`, datos);
      
      setVerificacionActual(data);
      toast.success('Observaciones guardadas');
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al actualizar verificación';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error actualizando verificación ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Elimina una verificación (soft delete, solo socios)
   * 
   * @param {string} id - UUID de la verificación
   */
  const eliminarVerificacion = useCallback(async (id) => {
    const confirmacion = window.confirm(
      '¿Estás seguro de eliminar esta verificación? Esta acción no se puede deshacer.'
    );
    
    if (!confirmacion) return null;

    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.delete(`/api/ala/verificaciones/${id}`);
      
      toast.success(data.mensaje || 'Verificación eliminada');
      
      // Limpiar verificación actual si es la eliminada
      if (verificacionActual?.id === id) {
        setVerificacionActual(null);
      }
      
      // Refrescar lista
      await cargarVerificaciones();
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al eliminar verificación';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error eliminando verificación ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [verificacionActual, cargarVerificaciones]);

  /**
   * Carga metadata de las listas ALA (solo socios)
   * Estado de cada lista: PEP, ONU, OFAC, UE
   */
  const cargarMetadataListas = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const { data } = await axiosClient.get('/api/ala/listas/metadata');
      
      setMetadataListas(data || []);
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al cargar metadata de listas';
      setError(errorMsg);
      // No mostrar toast para este error (puede ser 403 para no-socios)
      console.error('Error cargando metadata listas ALA:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Ejecuta búsquedas automáticas Art. 44 C.4 para una verificación
   * (Wikipedia + Google/IA + Noticias/IA)
   * 
   * NOTA: Este endpoint tarda 10-20 segundos (3 búsquedas)
   * 
   * @param {string} verificacionId - UUID de la verificación
   */
  const ejecutarBusquedasArt44 = useCallback(async (verificacionId) => {
    try {
      setLoadingBusquedas(true);
      setError(null);
      
      toast.loading('Ejecutando búsquedas Art. 44...', { id: 'busquedas-art44' });
      
      const { data } = await axiosClient.post(`/api/ala/verificaciones/${verificacionId}/busquedas-art44`);
      
      setVerificacionActual(data);
      toast.success('Búsquedas completadas', { id: 'busquedas-art44' });
      
      return data;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al ejecutar búsquedas';
      setError(errorMsg);
      toast.error(errorMsg, { id: 'busquedas-art44' });
      console.error('Error ejecutando búsquedas Art. 44:', err);
      return null;
    } finally {
      setLoadingBusquedas(false);
    }
  }, []);

  /**
   * Limpia la verificación actual
   */
  const limpiarVerificacionActual = useCallback(() => {
    setVerificacionActual(null);
    setError(null);
  }, []);

  /**
   * Descarga certificado PDF de una verificación ALA
   * 
   * @param {string} verificacionId - UUID de la verificación
   */
  const descargarCertificadoPDF = useCallback(async (verificacionId) => {
    try {
      setLoading(true);
      setError(null);
      
      toast.loading('Generando certificado PDF...', { id: 'certificado-pdf' });
      
      const response = await axiosClient.post(
        `/api/ala/verificaciones/${verificacionId}/certificado-pdf`,
        {},
        { responseType: 'blob' }
      );
      
      // Crear URL del blob
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      
      // Obtener nombre del archivo del header o usar uno por defecto
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'certificado_ala.pdf';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }
      
      // Crear link temporal y hacer click
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Liberar URL
      window.URL.revokeObjectURL(url);
      
      toast.success('Certificado descargado', { id: 'certificado-pdf' });
      
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al descargar certificado';
      setError(errorMsg);
      toast.error(errorMsg, { id: 'certificado-pdf' });
      console.error('Error descargando certificado PDF:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // Estado
    verificaciones,
    verificacionActual,
    metadataListas,
    loading,
    loadingBusquedas,
    error,
    totalVerificaciones,
    
    // Acciones
    ejecutarVerificacion,
    cargarVerificaciones,
    obtenerVerificacion,
    actualizarVerificacion,
    eliminarVerificacion,
    cargarMetadataListas,
    ejecutarBusquedasArt44,
    limpiarVerificacionActual,
    descargarCertificadoPDF,
    
    // Setters directos (para casos especiales)
    setVerificacionActual,
  };
}

export default useALA;
