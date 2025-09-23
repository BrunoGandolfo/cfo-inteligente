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
    <div className="px-6 mb-4 flex items-center gap-2">
      <span className="text-sm text-gray-600 dark:text-gray-400">Filtros activos:</span>

      {format(from, 'MM/yyyy') !== format(new Date(), 'MM/yyyy') && (
        <div className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 rounded-full text-sm">
          <span>{format(from, 'dd/MM', { locale: es })} - {format(to, 'dd/MM', { locale: es })}</span>
          <button onClick={resetDateFilter} className="ml-1 hover:text-blue-600">
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      {localidad !== 'Todas' && (
        <div className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900/20 text-purple-800 dark:text-purple-300 rounded-full text-sm">
          <span>{localidad}</span>
          <button onClick={resetLocalityFilter} className="ml-1 hover:text-purple-600">
            <X className="w-3 h-3" />
          </button>
        </div>
      )}

      <div className="inline-flex items-center px-3 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300 rounded-full text-sm">
        <span>{monedaVista}</span>
      </div>
    </div>
  );
}

export default ActiveFilters;


