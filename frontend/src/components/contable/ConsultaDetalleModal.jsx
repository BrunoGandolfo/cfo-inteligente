import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import Modal from '../ui/Modal';

function Campo({ label, children }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide font-semibold text-text-muted mb-0.5">
        {label}
      </p>
      <div className="text-sm text-text-primary">{children}</div>
    </div>
  );
}

function ConsultaDetalleModal({ consulta, open, onClose }) {
  if (!consulta) {
    return <Modal open={open} onClose={onClose} title="Detalle de consulta">Cargando…</Modal>;
  }

  const fecha = consulta.created_at ? new Date(consulta.created_at) : null;
  const exitosa = !!consulta.exitosa;

  return (
    <Modal open={open} onClose={onClose} title={`Consulta — ${consulta.servicio}`}>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <Campo label="Fecha">
            {fecha ? format(fecha, "dd/MM/yyyy HH:mm:ss", { locale: es }) : '-'}
          </Campo>
          <Campo label="Estado">
            <span className={exitosa ? 'text-success font-medium' : 'text-danger font-medium'}>
              {exitosa ? 'Exitosa' : 'Con error'}
            </span>
          </Campo>
          <Campo label="RUT">{consulta.rut || '-'}</Campo>
          <Campo label="CI">{consulta.ci || '-'}</Campo>
          <Campo label="Cliente">{consulta.cliente_nombre || '-'}</Campo>
          <Campo label="RUT cliente">{consulta.cliente_rut || '-'}</Campo>
        </div>

        {consulta.datos_entrada ? (
          <Campo label="Datos de entrada">
            <pre className="text-xs bg-surface-alt rounded-md p-3 overflow-x-auto">
              {JSON.stringify(consulta.datos_entrada, null, 2)}
            </pre>
          </Campo>
        ) : null}

        {consulta.resultado_texto ? (
          <Campo label="Resultado">
            <div className="text-sm bg-surface-alt rounded-md p-3 whitespace-pre-wrap break-words">
              {consulta.resultado_texto}
            </div>
          </Campo>
        ) : null}

        {consulta.error ? (
          <Campo label="Error">
            <div className="text-sm bg-danger/10 text-danger rounded-md p-3 whitespace-pre-wrap break-words">
              {consulta.error}
            </div>
          </Campo>
        ) : null}

        {consulta.resultado_datos ? (
          <Campo label="Datos crudos">
            <pre className="text-xs bg-surface-alt rounded-md p-3 overflow-x-auto max-h-64">
              {JSON.stringify(consulta.resultado_datos, null, 2)}
            </pre>
          </Campo>
        ) : null}
      </div>
    </Modal>
  );
}

export default ConsultaDetalleModal;
