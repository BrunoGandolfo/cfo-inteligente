/**
 * Página Contable — Servicios DGI
 *
 * Permite a usuarios autorizados consultar 10 servicios de la Dirección General
 * Impositiva (DGI) vía scraping automatizado + CapSolver, y revisar el historial
 * de consultas (con filtros por servicio y fecha).
 */

import { useEffect, useMemo, useState } from 'react';
import { Calculator, ChevronLeft, ChevronRight, Clock, RefreshCw } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import ServiceCard from '../components/contable/ServiceCard';
import ServiceForm from '../components/contable/ServiceForm';
import HistorialFiltros from '../components/contable/HistorialFiltros';
import HistorialTabla from '../components/contable/HistorialTabla';
import ConsultaDetalleModal from '../components/contable/ConsultaDetalleModal';
import { useContable } from '../hooks/useContable';
import { USUARIOS_ACCESO_CONTABLE } from '../utils/accessControl';

const LIMIT = 20;
const FILTROS_VACIOS = { servicio: '', fecha_desde: '', fecha_hasta: '' };

function Contable() {
  const esSocio = localStorage.getItem('esSocio') === 'true';
  const userEmail = (localStorage.getItem('userEmail') || '').toLowerCase();
  const tieneAcceso = esSocio || USUARIOS_ACCESO_CONTABLE.includes(userEmail);

  const {
    servicios,
    consultas,
    consultaActual,
    total,
    ultimosResultados,
    loadingServicios,
    loadingHistorial,
    loadingConsulta,
    cargarServicios,
    consultarServicio,
    cargarHistorial,
    obtenerConsulta,
    eliminarConsulta,
    limpiarResultado,
    setConsultaActual,
  } = useContable();

  const [servicioActivo, setServicioActivo] = useState(null);
  const [filtros, setFiltros] = useState(FILTROS_VACIOS);
  const [offset, setOffset] = useState(0);
  const [showDetalle, setShowDetalle] = useState(false);

  // Carga inicial: servicios + historial. Sólo si tiene acceso.
  useEffect(() => {
    if (!tieneAcceso) return;
    cargarServicios();
    cargarHistorial({ limit: LIMIT, offset: 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const aplicarFiltros = () => {
    setOffset(0);
    cargarHistorial({ ...filtros, limit: LIMIT, offset: 0 });
  };

  const limpiarFiltros = () => {
    setFiltros(FILTROS_VACIOS);
    setOffset(0);
    cargarHistorial({ limit: LIMIT, offset: 0 });
  };

  const irPagina = (nuevoOffset) => {
    setOffset(nuevoOffset);
    cargarHistorial({ ...filtros, limit: LIMIT, offset: nuevoOffset });
  };

  const handleConsultar = async (payload) => {
    const consulta = await consultarServicio(servicioActivo.id, payload);
    setServicioActivo(null);
    // Refrescar historial sin alterar la paginación visible
    cargarHistorial({ ...filtros, limit: LIMIT, offset });
    return consulta;
  };

  const handleVer = async (id) => {
    setShowDetalle(true);
    await obtenerConsulta(id);
  };

  const handleEliminar = async (id) => {
    const ok = await eliminarConsulta(id);
    if (ok && consultas.length === 1 && offset > 0) {
      // último registro de la página: retroceder una
      irPagina(Math.max(0, offset - LIMIT));
    }
  };

  const paginaActual = Math.floor(offset / LIMIT) + 1;
  const totalPaginas = Math.max(1, Math.ceil(total / LIMIT));

  const headerSubtitulo = useMemo(() => {
    if (esSocio) {
      return 'Consultas DGI automatizadas. Como socio, ves todas las consultas del equipo.';
    }
    return 'Consultá vigencia tributaria, declaraciones, exoneraciones y más servicios DGI.';
  }, [esSocio]);

  if (!tieneAcceso) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="bg-surface rounded-lg shadow p-8 border border-border text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
            <Calculator className="w-6 h-6 text-red-600 dark:text-red-400" />
          </div>
          <h1 className="text-xl font-semibold text-text-primary mb-2">
            Acceso restringido
          </h1>
          <p className="text-sm text-text-secondary">
            No tenés acceso a este módulo. Si creés que es un error, contactá a un administrador.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-soft text-accent shrink-0">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Servicios DGI</h1>
            <p className="text-sm text-text-secondary mt-1">{headerSubtitulo}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          onClick={() => cargarServicios()}
          disabled={loadingServicios}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loadingServicios ? 'animate-spin' : ''}`} />
          Refrescar servicios
        </Button>
      </div>

      {/* Grid de servicios */}
      {loadingServicios && servicios.length === 0 ? (
        <Card className="p-6">
          <div className="animate-pulse grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="h-32 bg-surface-alt rounded-lg" />
            <div className="h-32 bg-surface-alt rounded-lg" />
            <div className="h-32 bg-surface-alt rounded-lg" />
          </div>
        </Card>
      ) : servicios.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-sm text-text-secondary">
            No se pudieron cargar los servicios DGI. Probá refrescar.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {servicios.map(s => (
            <ServiceCard
              key={s.id}
              servicio={s}
              onConsultar={() => setServicioActivo(s)}
              loading={!!loadingConsulta[s.id]}
              ultimoResultado={ultimosResultados[s.id]}
              onLimpiarResultado={() => limpiarResultado(s.id)}
            />
          ))}
        </div>
      )}

      {/* Historial */}
      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-accent" />
            <h2 className="text-lg font-semibold text-text-primary">
              Historial de consultas
            </h2>
            {total > 0 ? (
              <span className="text-xs text-text-muted">({total} total)</span>
            ) : null}
          </div>
        </div>

        <div className="px-6 py-4 border-b border-border bg-surface-alt/40">
          <HistorialFiltros
            filtros={filtros}
            onChange={setFiltros}
            onAplicar={aplicarFiltros}
            onLimpiar={limpiarFiltros}
            servicios={servicios}
            loading={loadingHistorial}
          />
        </div>

        <HistorialTabla
          consultas={consultas}
          loading={loadingHistorial}
          mostrarUsuario={esSocio}
          onVer={handleVer}
          onEliminar={handleEliminar}
        />

        {total > LIMIT ? (
          <div className="px-6 py-3 border-t border-border flex items-center justify-between text-xs text-text-secondary">
            <span>
              Página {paginaActual} de {totalPaginas}
            </span>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => irPagina(Math.max(0, offset - LIMIT))}
                disabled={offset === 0 || loadingHistorial}
                className="flex items-center gap-1 !px-3 !py-1.5"
              >
                <ChevronLeft className="w-4 h-4" />
                Anterior
              </Button>
              <Button
                variant="ghost"
                onClick={() => irPagina(offset + LIMIT)}
                disabled={offset + LIMIT >= total || loadingHistorial}
                className="flex items-center gap-1 !px-3 !py-1.5"
              >
                Siguiente
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        ) : null}
      </Card>

      {/* Modal de formulario por servicio */}
      <ServiceForm
        servicio={servicioActivo}
        isOpen={!!servicioActivo}
        onClose={() => setServicioActivo(null)}
        onSubmit={handleConsultar}
        isLoading={servicioActivo ? !!loadingConsulta[servicioActivo.id] : false}
      />

      {/* Modal de detalle del historial */}
      <ConsultaDetalleModal
        consulta={consultaActual}
        open={showDetalle}
        onClose={() => { setShowDetalle(false); setConsultaActual(null); }}
      />
    </div>
  );
}

export default Contable;
