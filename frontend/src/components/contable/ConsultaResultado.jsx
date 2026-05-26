import { CheckCircle2, XCircle, X } from 'lucide-react';

function ConsultaResultado({ resultado, onLimpiar }) {
  if (!resultado) return null;
  const exitosa = !!resultado.exitosa;

  const bg = exitosa
    ? 'bg-success/10 border-success/30'
    : 'bg-danger/10 border-danger/30';
  const text = exitosa ? 'text-success' : 'text-danger';
  const Icon = exitosa ? CheckCircle2 : XCircle;

  const cuerpo = exitosa
    ? (resultado.resultado_texto || 'Consulta completada')
    : (resultado.error || resultado.resultado_texto || 'La consulta no pudo completarse');

  return (
    <div className={`relative mt-1 border rounded-md p-3 text-xs ${bg}`}>
      {onLimpiar ? (
        <button
          type="button"
          onClick={onLimpiar}
          className="absolute top-1.5 right-1.5 text-text-muted hover:text-text-secondary"
          aria-label="Limpiar resultado"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      ) : null}
      <div className={`flex items-start gap-2 ${text}`}>
        <Icon className="w-4 h-4 shrink-0 mt-0.5" />
        <div className="min-w-0 pr-4">
          <p className="font-semibold uppercase tracking-wide text-[10px]">
            {exitosa ? 'Resultado' : 'Error'}
          </p>
          <p className="mt-0.5 text-text-primary whitespace-pre-wrap break-words">
            {cuerpo}
          </p>
        </div>
      </div>
    </div>
  );
}

export default ConsultaResultado;
