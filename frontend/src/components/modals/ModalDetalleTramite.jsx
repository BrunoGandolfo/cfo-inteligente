import {
  X,
  FileText,
  Calendar,
  User,
  Clock,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

const RELATIVE_TIME_FORMATTER = new Intl.RelativeTimeFormat('es', {
  numeric: 'auto',
});

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

function formatDate(value) {
  if (!value) return 'Sin dato';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString('es-UY');
}

function getEstadoMeta(estado) {
  const normalized = normalizeText(estado);

  if (normalized === 'definitivo') {
    return {
      label: estado || 'Definitivo',
      className: 'bg-success/10 text-success border-success/20',
      icon: CheckCircle,
    };
  }

  if (normalized === 'provisoria' || normalized === 'provisorio') {
    return {
      label: estado || 'Provisoria',
      className: 'bg-warning/10 text-warning border-warning/20',
      icon: AlertTriangle,
    };
  }

  if (normalized === 'observado' || normalized === 'sin calificar') {
    return {
      label: estado || 'Sin calificar',
      className: 'bg-surface-alt text-text-secondary border-border',
      icon: Clock,
    };
  }

  return {
    label: estado || 'Sin dato',
    className: 'bg-surface-alt text-text-secondary border-border',
    icon: Clock,
  };
}

function parseActos(actos) {
  if (!actos) return [];

  try {
    const parsed = JSON.parse(actos);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function DetailItem({ icon, label, value }) {
  const IconComponent = icon;

  return (
    <div className="rounded-xl border border-border bg-surface-alt/60 p-4">
      <div className="mb-2 flex items-center gap-2 text-sm text-text-secondary">
        <IconComponent size={16} className="text-accent" />
        <span>{label}</span>
      </div>
      <div className="text-sm font-medium text-text-primary">
        {value || 'Sin dato'}
      </div>
    </div>
  );
}

export default function ModalDetalleTramite({ isOpen, onClose, tramite }) {
  if (!isOpen || !tramite) return null;

  const estadoMeta = getEstadoMeta(tramite.estado_actual);
  const EstadoIcon = estadoMeta.icon;
  const inscripciones = parseActos(tramite.actos);
  const registroLabel = tramite.registro_nombre || tramite.registro || 'Sin registro';
  const oficinaLabel = tramite.oficina_nombre || tramite.oficina || 'Sin oficina';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl animate-modal-enter rounded-xl border border-border bg-surface shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 border-b border-border p-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-xl font-semibold text-text-primary">
                {registroLabel} - {oficinaLabel}
              </h2>
              <span
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${estadoMeta.className}`}
              >
                <EstadoIcon size={14} />
                {estadoMeta.label}
              </span>
            </div>
            <p className="text-sm text-text-secondary">
              Detalle completo del trámite registral consultado en DGR.
            </p>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-2 text-text-muted transition-colors hover:bg-surface-alt hover:text-text-primary"
            type="button"
            aria-label="Cerrar modal"
          >
            <X size={22} />
          </button>
        </div>

        <div className="space-y-6 p-6">
          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <FileText size={18} className="text-accent" />
              <h3 className="text-lg font-semibold text-text-primary">Identificación</h3>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <DetailItem
                icon={FileText}
                label="Documento"
                value={`${tramite.anio || 'S/A'}/${tramite.numero_entrada || 'S/N'}`}
              />
              <DetailItem
                icon={Calendar}
                label="Fecha ingreso"
                value={formatDate(tramite.fecha_ingreso)}
              />
              <DetailItem
                icon={User}
                label="Escribano emisor"
                value={tramite.escribano_emisor}
              />
              <DetailItem
                icon={Clock}
                label="Último chequeo"
                value={formatRelativeTime(tramite.ultimo_chequeo)}
              />
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle size={18} className="text-accent" />
              <h3 className="text-lg font-semibold text-text-primary">Inscripciones</h3>
            </div>

            {inscripciones.length > 0 ? (
              <div className="overflow-hidden rounded-xl border border-border">
                <div className="grid grid-cols-[1.6fr_1fr] bg-surface-alt px-4 py-3 text-xs font-semibold uppercase tracking-wide text-text-secondary">
                  <span>Acto</span>
                  <span>Estado</span>
                </div>
                <div className="divide-y divide-border">
                  {inscripciones.map((inscripcion, index) => {
                    const inscripcionEstado = getEstadoMeta(inscripcion?.estado);
                    return (
                      <div
                        key={`${inscripcion?.acto || 'acto'}-${index}`}
                        className="grid grid-cols-[1.6fr_1fr] items-center gap-4 px-4 py-3"
                      >
                        <span className="text-sm text-text-primary">
                          {inscripcion?.acto || 'Sin acto'}
                        </span>
                        <span
                          className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-medium ${inscripcionEstado.className}`}
                        >
                          {inscripcionEstado.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-border bg-surface-alt/40 px-4 py-6 text-sm text-text-secondary">
                Sin inscripciones registradas
              </div>
            )}
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-warning" />
              <h3 className="text-lg font-semibold text-text-primary">Observaciones</h3>
            </div>

            {tramite.observaciones ? (
              <div className="rounded-xl border border-warning/20 bg-warning/10 p-4 text-sm text-text-primary whitespace-pre-wrap">
                {tramite.observaciones}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-border bg-surface-alt/40 px-4 py-6 text-sm text-text-secondary">
                Sin observaciones
              </div>
            )}
          </section>
        </div>

        <div className="flex justify-center border-t border-border p-6">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
