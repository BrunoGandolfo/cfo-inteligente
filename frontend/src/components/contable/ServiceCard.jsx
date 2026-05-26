import { Search, RefreshCw } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import ConsultaResultado from './ConsultaResultado';

function ServiceCard({ servicio, onConsultar, loading, ultimoResultado, onLimpiarResultado }) {
  return (
    <Card className="p-5 flex flex-col gap-3 h-full">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-text-primary leading-tight">
            {servicio.nombre}
          </h3>
          <p className="text-xs text-text-secondary mt-1 line-clamp-3">
            {servicio.descripcion}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1 flex-wrap">
        {servicio.campos?.map(c => (
          <span
            key={c}
            className="text-[10px] uppercase tracking-wide font-medium px-2 py-0.5 rounded-full bg-surface-alt text-text-secondary"
          >
            {c}
          </span>
        ))}
      </div>

      <div className="mt-auto">
        <Button
          variant="primary"
          onClick={onConsultar}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Consultando…
            </>
          ) : (
            <>
              <Search className="w-4 h-4" />
              Consultar
            </>
          )}
        </Button>
      </div>

      {ultimoResultado ? (
        <ConsultaResultado
          resultado={ultimoResultado}
          onLimpiar={onLimpiarResultado}
        />
      ) : null}
    </Card>
  );
}

export default ServiceCard;
