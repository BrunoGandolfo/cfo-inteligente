import { X } from 'lucide-react';
import { useFilters } from '../../hooks/useFilters';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function ActiveFilters() {
  const { from, to, localidad, monedaVista, setFrom, setTo, setLocalidad, apply } = useFilters();

  const resetDateFilter = () => {
    const firstDay = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    const lastDay = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0);
    setFrom(firstDay);
    setTo(lastDay);
    apply();
  };

  const resetLocalityFilter = () => {
    setLocalidad('Todas');
    apply();
  };

  const hasActiveFilters = localidad !== 'Todas' || 
    format(from, 'MM/yyyy') !== format(new Date(), 'MM/yyyy');

  if (!hasActiveFilters) return null;

  return (
    <div className="px-4 xl:px-6 mb-4 flex items-center gap-2">
      <span className="text-sm text-text-secondary">Filtros activos:</span>

      {format(from, 'MM/yyyy') !== format(new Date(), 'MM/yyyy') ? (
        <div className="inline-flex items-center gap-1 px-3 py-1 bg-info/10 text-info rounded-full text-sm">
          <span>{format(from, 'dd/MM', { locale: es })} - {format(to, 'dd/MM', { locale: es })}</span>
          <button onClick={resetDateFilter} className="ml-1 hover:text-info">
            <X className="w-3 h-3" />
          </button>
        </div>
      ) : null}

      {localidad !== 'Todas' ? (
        <div className="inline-flex items-center gap-1 px-3 py-1 bg-distribucion/10 text-distribucion rounded-full text-sm">
          <span>{localidad}</span>
          <button onClick={resetLocalityFilter} className="ml-1 hover:text-distribucion">
            <X className="w-3 h-3" />
          </button>
        </div>
      ) : null}

      <div className="inline-flex items-center px-3 py-1 bg-success/10 text-success rounded-full text-sm">
        <span>{monedaVista}</span>
      </div>
    </div>
  );
}

export default ActiveFilters;
