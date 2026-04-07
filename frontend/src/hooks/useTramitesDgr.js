import { useState, useCallback } from 'react';
import axiosClient from '../services/api/axiosClient';
import toast from 'react-hot-toast';

export const REGISTROS_DGR = {
  RGI: 'Registro Nacional de Actos Personales',
  RPI: 'Registro de la Propiedad, Sección Inmobiliaria',
  RAE: 'Registro de la Propiedad, Sección Mobiliaria, Aeronaves',
  RA: 'Registro de la Propiedad, Sección Mobiliaria, Automotores',
  PSD: 'Registro de la Propiedad, Sección Mobiliaria, Prenda S/Despl.',
  RCO: 'Registro de Personas Jurídicas',
  ACF: 'Registro de Personas Jurídicas Sec. Asoc. Civ. y Fundaciones',
  RUB: 'Registro de Rúbrica de Libros',
};

export const OFICINAS_DGR = {
  G: 'Artigas',
  A: 'Canelones',
  E: 'Cerro Largo',
  L: 'Colonia',
  S: 'La Costa',
  Q: 'Durazno',
  N: 'Flores',
  O: 'Florida',
  P: 'Lavalleja',
  B: 'Maldonado',
  X: 'Montevideo',
  W: 'Pando',
  I: 'Paysandu',
  J: 'Rio Negro',
  F: 'Rivera',
  C: 'Rocha',
  H: 'Salto',
  M: 'San Jose',
  K: 'Soriano',
  R: 'Tacuarembo',
  D: 'Treinta y Tres',
};

export function useTramitesDgr() {
  const [tramites, setTramites] = useState([]);
  const [pendientes, setPendientes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(null);

  /**
   * Lista trámites con filtros opcionales
   */
  const fetchTramites = useCallback(async (filtros = {}) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        activo: filtros.activo ?? true,
        limit: filtros.limit || 50,
        offset: filtros.offset || 0,
        registro: filtros.registro,
        oficina: filtros.oficina,
      };

      Object.keys(params).forEach((key) =>
        params[key] === undefined && delete params[key]
      );

      const { data } = await axiosClient.get('/api/tramites-dgr/', { params });
      const lista = data.tramites || data.items || data.results || [];

      setTramites(lista);
      setTotal(data.total ?? data.count ?? lista.length ?? 0);

      return data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || 'Error al cargar trámites DGR';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando trámites DGR:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Crea un nuevo trámite
   */
  const crearTramite = useCallback(
    async (tramiteData) => {
      try {
        setLoading(true);
        setError(null);

        const { data } = await axiosClient.post('/api/tramites-dgr/', tramiteData);

        toast.success('Trámite creado correctamente');

        await fetchTramites();
        await fetchPendientes();

        return data;
      } catch (err) {
        const errorMsg =
          err.response?.data?.detail || err.message || 'Error al crear trámite DGR';
        setError(errorMsg);
        toast.error(errorMsg);
        console.error('Error creando trámite DGR:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fetchTramites, fetchPendientes]
  );

  /**
   * Sincroniza un trámite con DGR
   */
  const sincronizarTramite = useCallback(
    async (id) => {
      try {
        setLoading(true);
        setError(null);

        const { data } = await axiosClient.post(`/api/tramites-dgr/${id}/sincronizar`);

        toast.success(data.mensaje || 'Trámite sincronizado correctamente');

        await fetchTramites();
        await fetchPendientes();

        return data;
      } catch (err) {
        const errorMsg =
          err.response?.data?.detail || err.message || 'Error al sincronizar trámite DGR';
        setError(errorMsg);
        toast.error(errorMsg);
        console.error('Error sincronizando trámite DGR:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fetchTramites, fetchPendientes]
  );

  /**
   * Elimina un trámite
   */
  const eliminarTramite = useCallback(
    async (id) => {
      const confirmacion = window.confirm(
        '¿Estás seguro de eliminar este trámite? Esta acción no se puede deshacer.'
      );

      if (!confirmacion) return null;

      try {
        setLoading(true);
        setError(null);

        const { data } = await axiosClient.delete(`/api/tramites-dgr/${id}`);

        toast.success(data.mensaje || 'Trámite eliminado correctamente');

        await fetchTramites();
        await fetchPendientes();

        return data;
      } catch (err) {
        const errorMsg =
          err.response?.data?.detail || err.message || 'Error al eliminar trámite DGR';
        setError(errorMsg);
        toast.error(errorMsg);
        console.error('Error eliminando trámite DGR:', err);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fetchTramites, fetchPendientes]
  );

  /**
   * Carga trámites pendientes de revisión
   */
  const fetchPendientes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const { data } = await axiosClient.get('/api/tramites-dgr/pendientes');
      const lista = Array.isArray(data)
        ? data
        : data.pendientes || data.items || data.results || [];

      setPendientes(lista);

      return data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || 'Error al cargar pendientes DGR';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error cargando pendientes DGR:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Marca pendientes como notificados
   */
  const marcarNotificados = useCallback(async (ids = []) => {
    try {
      setLoading(true);
      setError(null);

      const { data } = await axiosClient.post('/api/tramites-dgr/pendientes/marcar-notificados', {
        ids,
      });

      toast.success(data.mensaje || 'Pendientes marcados como notificados');

      await fetchPendientes();

      return data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail || err.message || 'Error al marcar notificados DGR';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error marcando notificados DGR:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchPendientes]);

  return {
    tramites,
    loading,
    total,
    fetchTramites,
    crearTramite,
    sincronizarTramite,
    eliminarTramite,
    pendientes,
    fetchPendientes,
    marcarNotificados,
    error,
  };
}

export default useTramitesDgr;
