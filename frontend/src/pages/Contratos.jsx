import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useContratos } from '../hooks/useContratos';
import ModalDetalleTramite from '../components/modals/ModalDetalleTramite';
import {
  REGISTROS_DGR,
  OFICINAS_DGR,
  useTramitesDgr,
} from '../hooks/useTramitesDgr';
import axiosClient from '../services/api/axiosClient';
import {
  AlertTriangle,
  Building2,
  CheckCircle,
  ChevronDown,
  Clock,
  FileCheck,
  FileText,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react';

const RELATIVE_TIME_FORMATTER = new Intl.RelativeTimeFormat('es', {
  numeric: 'auto',
});

function createTramiteForm() {
  return {
    registro: '',
    oficina: '',
    anio: String(new Date().getFullYear()),
    numero_entrada: '',
    bis: '',
  };
}

function normalizeText(value) {
  if (value == null) return '';
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function formatRelativeTime(value) {
  if (!value) return 'sin chequeo';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'sin chequeo';

  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000);
  const units = [
    ['year', 60 * 60 * 24 * 365],
    ['month', 60 * 60 * 24 * 30],
    ['day', 60 * 60 * 24],
    ['hour', 60 * 60],
    ['minute', 60],
    ['second', 1],
  ];

  for (const [unit, size] of units) {
    if (Math.abs(diffSeconds) >= size || unit === 'second') {
      return RELATIVE_TIME_FORMATTER.format(Math.round(diffSeconds / size), unit);
    }
  }

  return 'sin chequeo';
}

function getTramiteEstadoMeta(estadoActual, cambioDetectado) {
  const normalized = normalizeText(estadoActual);

  if (normalized === 'definitivo') {
    return {
      label: estadoActual || 'Definitivo',
      className: 'bg-success/10 text-success border-success/20',
      icon: CheckCircle,
    };
  }

  if (normalized === 'provisorio') {
    return {
      label: estadoActual || 'Provisorio',
      className: 'bg-warning/10 text-warning border-warning/20',
      icon: AlertTriangle,
    };
  }

  if (normalized === 'observado') {
    return {
      label: estadoActual || 'Observado',
      className: 'bg-danger/10 text-danger border-danger/20',
      icon: AlertTriangle,
    };
  }

  if (normalized === 'pendiente') {
    return {
      label: estadoActual || 'Pendiente',
      className: 'bg-surface-alt text-text-secondary border-border',
      icon: Clock,
    };
  }

  return {
    label: estadoActual || 'Pendiente',
    className: cambioDetectado
      ? 'bg-warning/10 text-warning border-warning/20'
      : 'bg-surface-alt text-text-secondary border-border',
    icon: cambioDetectado ? AlertTriangle : Clock,
  };
}

function getRegistroNombre(registro) {
  return REGISTROS_DGR[registro] || registro || 'Sin registro';
}

function getOficinaNombre(oficina) {
  return OFICINAS_DGR[oficina] || oficina || 'Sin oficina';
}

function Contratos() {
  const {
    contratos,
    loading: loadingContratos,
    error: errorContratos,
    total,
    fetchContratos,
    fetchContrato,
    contratoActual,
  } = useContratos();
  const {
    tramites,
    loading: loadingTramitesDgr,
    total: totalTramitesDgr,
    fetchTramites,
    crearTramite,
    sincronizarTramite,
    eliminarTramite,
    pendientes,
    fetchPendientes,
    error: errorTramitesDgr,
  } = useTramitesDgr();

  const [contratoSeleccionadoId, setContratoSeleccionadoId] = useState('');
  const [valoresCampos, setValoresCampos] = useState({});
  const [todosContratos, setTodosContratos] = useState([]);
  const [activeTab, setActiveTab] = useState('contratos');
  const [tramiteModalOpen, setTramiteModalOpen] = useState(false);
  const [tramiteForm, setTramiteForm] = useState(createTramiteForm);
  const [tramiteDetalleOpen, setTramiteDetalleOpen] = useState(false);
  const [tramiteSeleccionado, setTramiteSeleccionado] = useState(null);

  // Cargar todos los contratos al montar (en múltiples llamadas si hay más de 100)
  useEffect(() => {
    const cargarTodosContratos = async () => {
      try {
        // Primera llamada: primeros 100
        const primera = await fetchContratos({ limit: 100, skip: 0 });
        const totalContratos = primera?.total || 0;
        let contratosAcumulados = [...(primera?.contratos || [])];

        // Si hay más de 100, cargar el resto en llamadas adicionales
        if (totalContratos > 100) {
          const llamadasAdicionales = Math.ceil((totalContratos - 100) / 100);
          for (let i = 1; i <= llamadasAdicionales; i += 1) {
            const siguiente = await fetchContratos({ limit: 100, skip: i * 100 });
            if (siguiente?.contratos) {
              contratosAcumulados = [...contratosAcumulados, ...siguiente.contratos];
            }
          }
        }

        // Actualizar estado local con todos los contratos
        setTodosContratos(contratosAcumulados);
      } catch (err) {
        console.error('Error cargando contratos:', err);
      }
    };

    cargarTodosContratos();
  }, [fetchContratos]);

  useEffect(() => {
    if (activeTab !== 'seguimiento-registral') {
      setTramiteModalOpen(false);
      return;
    }

    fetchTramites({ activo: true, limit: 50 });
    fetchPendientes();
  }, [activeTab, fetchPendientes, fetchTramites]);

  // Cargar contrato cuando se selecciona
  useEffect(() => {
    if (contratoSeleccionadoId) {
      fetchContrato(contratoSeleccionadoId);
      setValoresCampos({}); // Resetear valores al cambiar contrato
    }
  }, [contratoSeleccionadoId, fetchContrato]);

  // Usar todosContratos si está disponible, sino usar contratos del hook
  const contratosDisponibles = todosContratos.length > 0 ? todosContratos : contratos;

  // Ordenar contratos alfabéticamente
  const contratosOrdenados = [...contratosDisponibles].sort((a, b) =>
    a.titulo.localeCompare(b.titulo)
  );
  const tieneContratoSeleccionado = Boolean(contratoActual) && Boolean(contratoSeleccionadoId);
  const tieneCamposEditables = (contratoActual?.campos_editables?.campos?.length || 0) > 0;
  const tramitesPendientes = pendientes || [];
  const cambiosSinRevisar = tramitesPendientes.filter((tramite) => tramite?.cambio_detectado).length;

  const handleSelectContrato = (e) => {
    setContratoSeleccionadoId(e.target.value);
  };

  const handleCampoChange = (campoId, valor) => {
    setValoresCampos((prev) => ({
      ...prev,
      [campoId]: valor,
    }));
  };

  const handleGenerarContrato = async (e) => {
    e.preventDefault();

    if (!contratoSeleccionadoId || !contratoActual) {
      toast.error('Por favor selecciona un contrato');
      return;
    }

    try {
      const response = await axiosClient.post(
        `/api/contratos/${contratoSeleccionadoId}/generar`,
        { valores: valoresCampos },
        { responseType: 'blob' }
      );

      // Descargar el archivo
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${contratoActual.titulo.replace(/\s+/g, '_')}_completado.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Contrato generado y descargado exitosamente');
    } catch (err) {
      console.error('Error generando contrato:', err);
      toast.error(err.message || 'Error al generar el contrato');
    }
  };

  const abrirModalTramite = () => {
    setTramiteForm(createTramiteForm());
    setTramiteModalOpen(true);
  };

  const abrirDetalleTramite = (tramite) => {
    setTramiteSeleccionado(tramite);
    setTramiteDetalleOpen(true);
  };

  const cerrarDetalleTramite = () => {
    setTramiteDetalleOpen(false);
    setTramiteSeleccionado(null);
  };

  const cerrarModalTramite = () => {
    setTramiteModalOpen(false);
    setTramiteForm(createTramiteForm());
  };

  const handleTramiteFormChange = (campo, value) => {
    setTramiteForm((prev) => ({
      ...prev,
      [campo]: value,
    }));
  };

  const handleCrearTramite = async (e) => {
    e.preventDefault();

    if (!tramiteForm.registro || !tramiteForm.oficina || !tramiteForm.anio || !tramiteForm.numero_entrada) {
      toast.error('Completa registro, oficina, año y número de entrada');
      return;
    }

    const data = await crearTramite({
      registro: tramiteForm.registro,
      oficina: tramiteForm.oficina,
      anio: Number(tramiteForm.anio),
      numero_entrada: Number(tramiteForm.numero_entrada),
      bis: tramiteForm.bis.trim(),
    });

    if (data) {
      cerrarModalTramite();
    }
  };

  const renderContratosTab = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Estadísticas */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-accent" />
            <span className="text-lg font-semibold text-text-primary">
              Total de contratos: <span className="text-accent">{total}</span>
            </span>
          </div>
        </div>

        {/* Dropdown de selección */}
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="relative">
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted pointer-events-none" />
            <select
              value={contratoSeleccionadoId}
              onChange={handleSelectContrato}
              className="w-full pl-4 pr-10 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent appearance-none"
            >
              <option value="">Seleccionar contrato...</option>
              {contratosOrdenados.map((contrato) => (
                <option key={contrato.id} value={contrato.id}>
                  {contrato.titulo}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Mensaje de advertencia */}
      <div className="bg-warning/10 border border-warning/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-warning text-xl">⚠️</span>
          <div>
            <p className="font-semibold text-warning mb-1">
              Importante sobre los contratos
            </p>
            <p className="text-sm text-text-secondary">
              Algunos contratos están completos y listos para usar. Otros son <strong>modelos de ejemplo</strong> donde, al completar los campos, algunos valores aparecerán en el documento y otros no. Los datos ingresados quedarán en los lugares correctos. <strong>El documento Word descargado puede requerir revisión y ajustes adicionales.</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Detalle del contrato seleccionado */}
      {tieneContratoSeleccionado ? (
        <div className="bg-surface border border-border rounded-lg shadow-sm p-4 md:p-6">
          <div className="mb-6">
            <h2 className="text-xl md:text-2xl font-bold text-text-primary mb-2">
              {contratoActual.titulo}
            </h2>
            <p className="text-text-secondary">
              Categoría: <span className="font-medium">{contratoActual.categoria?.charAt(0).toUpperCase() + contratoActual.categoria?.slice(1).replace(/_/g, ' ') || 'Sin categoría'}</span>
            </p>
            {contratoActual.campos_editables ? (
              <p className="text-sm text-text-muted mt-1">
                {contratoActual.campos_editables.total_campos || 0} campos editables
              </p>
            ) : null}
          </div>

          {/* Formulario de campos */}
          {tieneCamposEditables ? (
            <form onSubmit={handleGenerarContrato} className="space-y-4">
              <div className="mb-4 p-3 bg-success/10 border border-success/30 rounded-lg">
                <p className="text-sm text-success">
                  Todos los campos son opcionales. Complete solo los que necesite.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {contratoActual.campos_editables.campos
                  .sort((a, b) => (a.orden || 0) - (b.orden || 0))
                  .map((campo) => (
                    <div key={campo.id} className="space-y-1">
                      <label className="block text-sm font-medium text-text-secondary">
                        {campo.nombre}
                      </label>
                      <input
                        type="text"
                        value={valoresCampos[campo.id] || ''}
                        onChange={(e) => handleCampoChange(campo.id, e.target.value)}
                        placeholder={campo.placeholder_original || campo.contexto || 'Ingrese el valor...'}
                        className="w-full px-4 py-2 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                      />
                      {campo.contexto ? (
                        <p className="text-xs text-text-muted italic">
                          {campo.contexto}
                        </p>
                      ) : null}
                    </div>
                  ))}
              </div>

              <div className="pt-4 border-t border-border">
                <button
                  type="submit"
                  className="w-full px-6 py-3 bg-accent hover:bg-accent-hover text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                  <FileCheck className="w-5 h-5" />
                  Generar Contrato
                </button>
              </div>
            </form>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">
                Este contrato no tiene campos editables disponibles
              </p>
            </div>
          )}
        </div>
      ) : null}

      {/* Estado inicial - sin contrato seleccionado */}
      {!contratoSeleccionadoId ? (
        <div className="bg-surface border border-border rounded-lg shadow-sm">
          {loadingContratos ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
              <p className="mt-4 text-text-secondary">Cargando contratos...</p>
            </div>
          ) : errorContratos ? (
            <div className="p-8 text-center">
              <p className="text-danger">
                {typeof errorContratos === 'string' ? errorContratos : errorContratos?.message || errorContratos?.msg || 'Error desconocido'}
              </p>
            </div>
          ) : contratosOrdenados.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">
                No hay contratos disponibles
              </p>
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-text-secondary">
                Selecciona un contrato del dropdown para comenzar
              </p>
            </div>
          )}
        </div>
      ) : null}
    </>
  );

  const renderSeguimientoRegistral = () => (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
            Seguimiento Registral
          </h1>
          <p className="mt-2 text-text-secondary">
            Monitoreo automático de trámites en DGR
          </p>
          <p className="mt-1 text-sm text-text-muted">
            Total en seguimiento: {totalTramitesDgr}
          </p>
        </div>
        <button
          type="button"
          onClick={abrirModalTramite}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent text-white font-semibold hover:bg-accent-hover transition-colors"
        >
          <Plus className="w-4 h-4" />
          Agregar trámite
        </button>
      </div>

      {cambiosSinRevisar > 0 ? (
        <div className="bg-warning/10 border border-warning/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-warning mt-0.5" />
            <div>
              <p className="font-semibold text-warning">
                {cambiosSinRevisar} trámites tienen cambios sin revisar
              </p>
              <p className="text-sm text-text-secondary mt-1">
                Revisá y sincronizá los trámites detectados antes de marcarlos como notificados.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="bg-surface border border-border rounded-lg shadow-sm">
        {loadingTramitesDgr && tramites.length === 0 ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
            <p className="mt-4 text-text-secondary">Cargando trámites registrales...</p>
          </div>
        ) : errorTramitesDgr ? (
          <div className="p-8 text-center">
            <p className="text-danger">
              {typeof errorTramitesDgr === 'string'
                ? errorTramitesDgr
                : errorTramitesDgr?.message || errorTramitesDgr?.msg || 'Error desconocido'}
            </p>
          </div>
        ) : tramites.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="w-12 h-12 text-text-muted mx-auto mb-4" />
            <p className="text-text-secondary">
              No hay trámites en seguimiento
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border">
            {tramites.map((tramite) => {
              const estadoMeta = getTramiteEstadoMeta(tramite.estado_actual, tramite.cambio_detectado);
              const EstadoIcon = estadoMeta.icon;

              return (
                <div
                  key={tramite.id}
                  className="p-4 md:p-6 cursor-pointer transition-colors hover:bg-surface-alt/50"
                  onClick={() => abrirDetalleTramite(tramite)}
                >
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="flex-1 space-y-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <Building2 className="w-5 h-5 text-accent" />
                            <h3 className="text-lg font-semibold text-text-primary">
                              {getRegistroNombre(tramite.registro)}
                            </h3>
                          </div>
                          <p className="text-sm text-text-secondary">
                            {getOficinaNombre(tramite.oficina)}
                          </p>
                        </div>

                        <span className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-full border ${estadoMeta.className}`}>
                          <EstadoIcon className="w-4 h-4" />
                          {estadoMeta.label}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                        <div className="rounded-lg bg-surface-alt border border-border p-3">
                          <p className="text-text-muted text-xs uppercase tracking-wide">Documento</p>
                          <p className="mt-1 font-semibold text-text-primary">
                            {tramite.anio}/{tramite.numero_entrada}
                            {tramite.bis ? ` ${tramite.bis}` : ''}
                          </p>
                        </div>
                        <div className="rounded-lg bg-surface-alt border border-border p-3">
                          <p className="text-text-muted text-xs uppercase tracking-wide">Escribano / Emisor</p>
                          <p className="mt-1 font-medium text-text-primary">
                            {tramite.escribano_emisor || 'Sin dato'}
                          </p>
                        </div>
                        <div className="rounded-lg bg-surface-alt border border-border p-3">
                          <div className="flex items-center gap-2 text-text-muted text-xs uppercase tracking-wide">
                            <Clock className="w-4 h-4" />
                            Último chequeo
                          </div>
                          <p className="mt-1 font-medium text-text-primary">
                            {formatRelativeTime(tramite.ultimo_chequeo)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 lg:justify-end">
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          abrirDetalleTramite(tramite);
                        }}
                        className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-text-primary hover:bg-surface-alt"
                      >
                        Ver detalle
                      </button>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          sincronizarTramite(tramite.id);
                        }}
                        disabled={loadingTramitesDgr}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-surface hover:bg-surface-alt text-text-primary disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        <RefreshCw className={`w-4 h-4 ${loadingTramitesDgr ? 'animate-spin' : ''}`} />
                        Sincronizar
                      </button>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          eliminarTramite(tramite.id);
                        }}
                        disabled={loadingTramitesDgr}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-surface hover:bg-danger/10 hover:text-danger disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        <Trash2 className="w-4 h-4" />
                        Eliminar
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {tramiteModalOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={cerrarModalTramite}
        >
          <div
            className="w-full max-w-2xl bg-surface border border-border rounded-xl shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div>
                <h2 className="text-lg font-semibold text-text-primary">
                  Agregar trámite
                </h2>
                <p className="text-sm text-text-secondary">
                  Cargá la identificación registral y consultá la DGR automáticamente.
                </p>
              </div>
              <button
                type="button"
                onClick={cerrarModalTramite}
                className="text-text-muted hover:text-text-primary"
              >
                Cerrar
              </button>
            </div>

            <form onSubmit={handleCrearTramite} className="p-5 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-text-secondary">
                    Registro
                  </label>
                  <select
                    value={tramiteForm.registro}
                    onChange={(e) => handleTramiteFormChange('registro', e.target.value)}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                  >
                    <option value="">Seleccionar registro...</option>
                    {Object.entries(REGISTROS_DGR).map(([codigo, nombre]) => (
                      <option key={codigo} value={codigo}>
                        {codigo} - {nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-text-secondary">
                    Oficina Registral
                  </label>
                  <select
                    value={tramiteForm.oficina}
                    onChange={(e) => handleTramiteFormChange('oficina', e.target.value)}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                  >
                    <option value="">Seleccionar oficina...</option>
                    {Object.entries(OFICINAS_DGR).map(([codigo, nombre]) => (
                      <option key={codigo} value={codigo}>
                        {codigo} - {nombre}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-text-secondary">
                    Año
                  </label>
                  <input
                    type="number"
                    min="1900"
                    max={new Date().getFullYear() + 1}
                    value={tramiteForm.anio}
                    onChange={(e) => handleTramiteFormChange('anio', e.target.value)}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-text-secondary">
                    N° de entrada
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={tramiteForm.numero_entrada}
                    onChange={(e) => handleTramiteFormChange('numero_entrada', e.target.value)}
                    className="w-full px-4 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-text-secondary">
                  Bis
                </label>
                <input
                  type="text"
                  value={tramiteForm.bis}
                  onChange={(e) => handleTramiteFormChange('bis', e.target.value)}
                  placeholder="Opcional"
                  className="w-full px-4 py-3 border border-border rounded-lg bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent"
                />
              </div>

              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={cerrarModalTramite}
                  className="px-4 py-2.5 rounded-lg border border-border bg-surface hover:bg-surface-alt text-text-primary"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loadingTramitesDgr}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent text-white font-semibold hover:bg-accent-hover disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {loadingTramitesDgr ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                  Agregar y consultar
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );

  return (
    <div className="p-4 lg:p-6 space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
            Módulo Notarial
          </h1>
          <p className="mt-2 text-text-secondary">
            Gestión de Contratos
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-border bg-surface p-1 shadow-sm">
          <button
            type="button"
            onClick={() => setActiveTab('contratos')}
            className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
              activeTab === 'contratos'
                ? 'bg-accent text-white'
                : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-alt'
            }`}
          >
            Contratos
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('seguimiento-registral')}
            className={`px-4 py-2 rounded-md text-sm font-semibold transition-colors ${
              activeTab === 'seguimiento-registral'
                ? 'bg-accent text-white'
                : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-alt'
            }`}
          >
            Seguimiento Registral
          </button>
        </div>
      </div>

      {activeTab === 'contratos' ? renderContratosTab() : renderSeguimientoRegistral()}

      <ModalDetalleTramite
        isOpen={tramiteDetalleOpen}
        onClose={cerrarDetalleTramite}
        tramite={tramiteSeleccionado}
      />
    </div>
  );
}

export default Contratos;
