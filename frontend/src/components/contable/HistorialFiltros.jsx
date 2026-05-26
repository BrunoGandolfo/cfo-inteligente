import { Filter, RotateCcw } from 'lucide-react';
import Button from '../ui/Button';

function HistorialFiltros({ filtros, onChange, onAplicar, onLimpiar, servicios, loading }) {
  const handleField = (campo) => (e) => {
    onChange({ ...filtros, [campo]: e.target.value });
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-end">
      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1">Servicio</label>
        <select
          value={filtros.servicio || ''}
          onChange={handleField('servicio')}
          disabled={loading}
          className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
        >
          <option value="">Todos</option>
          {servicios.map(s => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1">Desde</label>
        <input
          type="date"
          value={filtros.fecha_desde || ''}
          onChange={handleField('fecha_desde')}
          disabled={loading}
          className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
        />
      </div>

      <div>
        <label className="block text-xs font-medium text-text-secondary mb-1">Hasta</label>
        <input
          type="date"
          value={filtros.fecha_hasta || ''}
          onChange={handleField('fecha_hasta')}
          disabled={loading}
          className="w-full px-3 py-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:ring-2 focus:ring-accent focus:border-transparent disabled:opacity-50"
        />
      </div>

      <div className="flex gap-2">
        <Button
          variant="primary"
          onClick={onAplicar}
          disabled={loading}
          className="flex items-center gap-1.5"
        >
          <Filter className="w-4 h-4" />
          Filtrar
        </Button>
        <Button
          variant="ghost"
          onClick={onLimpiar}
          disabled={loading}
          className="flex items-center gap-1.5"
        >
          <RotateCcw className="w-4 h-4" />
          Limpiar
        </Button>
      </div>
    </div>
  );
}

export default HistorialFiltros;
