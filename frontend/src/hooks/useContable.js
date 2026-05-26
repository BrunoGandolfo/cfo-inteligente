/**
 * Hook para módulo Contable — Servicios DGI
 *
 * 10 servicios DGI vía scraping Playwright + CapSolver:
 * CERTIFICADO_UNICO, DECLARACION_IRPF, AFILIACION_BANCARIA, BORRADORES_IASS,
 * EXONERACION_ARRENDAMIENTOS, ESTADO_TRAMITE, EXPEDIENTE_ADMINISTRATIVO,
 * DEVOLUCION_IVA_GASOIL, CONSTANCIA_PRIMARIA, RESIDENCIA_FISCAL
 */

import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import axiosClient from '../services/api/axiosClient';

export function useContable() {
  const [servicios, setServicios] = useState([]);
  const [consultas, setConsultas] = useState([]);
  const [consultaActual, setConsultaActual] = useState(null);
  const [total, setTotal] = useState(0);

  // Granular loading: una consulta DGI puede tardar 30-60s; el historial
  // no debería quedar bloqueado mientras corre y viceversa.
  const [loadingServicios, setLoadingServicios] = useState(false);
  const [loadingHistorial, setLoadingHistorial] = useState(false);
  const [loadingConsulta, setLoadingConsulta] = useState({}); // {[servicioId]: bool}

  // Último resultado por servicio (para mostrar inline en la tarjeta).
  // {[servicioId]: { exitosa, resultado_texto, error, ... }}
  const [ultimosResultados, setUltimosResultados] = useState({});

  const [error, setError] = useState(null);

  const _extraerMensajeError = (err, fallback) => {
    if (err.response?.data?.detail) {
      if (Array.isArray(err.response.data.detail)) {
        return err.response.data.detail.map(e => e.msg || String(e)).join(', ');
      }
      return typeof err.response.data.detail === 'string'
        ? err.response.data.detail
        : String(err.response.data.detail);
    }
    return err.message || fallback;
  };

  const cargarServicios = useCallback(async () => {
    try {
      setLoadingServicios(true);
      setError(null);
      const { data } = await axiosClient.get('/api/contable/servicios-disponibles');
      setServicios(Array.isArray(data) ? data : []);
      return data;
    } catch (err) {
      const msg = _extraerMensajeError(err, 'Error al cargar servicios DGI');
      setError(msg);
      toast.error(msg);
      return null;
    } finally {
      setLoadingServicios(false);
    }
  }, []);

  const consultarServicio = useCallback(async (servicioId, payload = {}) => {
    setLoadingConsulta(prev => ({ ...prev, [servicioId]: true }));
    setError(null);
    try {
      const body = { servicio: servicioId, ...payload };
      const { data } = await axiosClient.post('/api/contable/consultar', body, {
        timeout: 120000,
      });
      const consulta = data?.consulta || null;
      if (consulta) {
        setUltimosResultados(prev => ({ ...prev, [servicioId]: consulta }));
        if (consulta.exitosa) {
          toast.success('Consulta DGI completada');
        } else {
          toast.error(consulta.error || 'La consulta no pudo completarse');
        }
      }
      return consulta;
    } catch (err) {
      const msg = _extraerMensajeError(err, 'Error al ejecutar la consulta DGI');
      setError(msg);
      toast.error(msg);
      // Persistimos el error inline para que el usuario pueda reintentar sin perder contexto.
      setUltimosResultados(prev => ({
        ...prev,
        [servicioId]: {
          exitosa: false,
          error: msg,
          resultado_texto: null,
          servicio: servicioId,
          created_at: new Date().toISOString(),
        },
      }));
      return null;
    } finally {
      setLoadingConsulta(prev => {
        const next = { ...prev };
        delete next[servicioId];
        return next;
      });
    }
  }, []);

  const cargarHistorial = useCallback(async (filtros = {}) => {
    try {
      setLoadingHistorial(true);
      setError(null);
      const params = {
        servicio: filtros.servicio,
        rut: filtros.rut,
        fecha_desde: filtros.fecha_desde,
        fecha_hasta: filtros.fecha_hasta,
        limit: filtros.limit ?? 50,
        offset: filtros.offset ?? 0,
      };
      Object.keys(params).forEach(k =>
        (params[k] === undefined || params[k] === null || params[k] === '') && delete params[k]
      );
      const { data } = await axiosClient.get('/api/contable/consultas', { params });
      setConsultas(data?.consultas || []);
      setTotal(data?.total || 0);
      return data;
    } catch (err) {
      const msg = _extraerMensajeError(err, 'Error al cargar el historial de consultas');
      setError(msg);
      toast.error(msg);
      return null;
    } finally {
      setLoadingHistorial(false);
    }
  }, []);

  const obtenerConsulta = useCallback(async (id) => {
    try {
      setError(null);
      const { data } = await axiosClient.get(`/api/contable/consultas/${id}`);
      const consulta = data?.consulta || null;
      setConsultaActual(consulta);
      return consulta;
    } catch (err) {
      const msg = _extraerMensajeError(err, 'Error al obtener la consulta');
      setError(msg);
      toast.error(msg);
      return null;
    }
  }, []);

  const eliminarConsulta = useCallback(async (id) => {
    const ok = window.confirm('¿Eliminar esta consulta del historial? Esta acción no se puede deshacer.');
    if (!ok) return false;
    try {
      setError(null);
      await axiosClient.delete(`/api/contable/consultas/${id}`);
      toast.success('Consulta eliminada del historial');
      setConsultas(prev => prev.filter(c => c.id !== id));
      setTotal(prev => Math.max(0, prev - 1));
      if (consultaActual?.id === id) setConsultaActual(null);
      return true;
    } catch (err) {
      const msg = _extraerMensajeError(err, 'Error al eliminar la consulta');
      setError(msg);
      toast.error(msg);
      return false;
    }
  }, [consultaActual]);

  const limpiarResultado = useCallback((servicioId) => {
    setUltimosResultados(prev => {
      const next = { ...prev };
      delete next[servicioId];
      return next;
    });
  }, []);

  return {
    // estado
    servicios,
    consultas,
    consultaActual,
    total,
    ultimosResultados,
    loadingServicios,
    loadingHistorial,
    loadingConsulta,
    error,
    // acciones
    cargarServicios,
    consultarServicio,
    cargarHistorial,
    obtenerConsulta,
    eliminarConsulta,
    limpiarResultado,
    setConsultaActual,
  };
}

export default useContable;
