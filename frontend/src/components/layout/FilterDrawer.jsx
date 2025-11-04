import { X, Filter } from 'lucide-react';
import PropTypes from 'prop-types';
import { useEffect } from 'react';
import MonedaToggle from '../filters/MonedaToggle';
import DateRangePicker from '../filters/DateRangePicker';
import LocalityFilter from '../filters/LocalityFilter';

/**
 * FilterDrawer - Drawer colapsable para filtros
 * 
 * Patrón: Slide-down drawer desde top (debajo del header)
 * Usado en: QuickBooks, Xero, Stripe Dashboard
 * 
 * Props:
 * - isOpen: boolean - Estado del drawer
 * - onClose: function - Callback para cerrar
 * - from: Date - Fecha inicio
 * - to: Date - Fecha fin
 * - localidad: string - Localidad seleccionada
 * - setFrom: function - Setter de fecha inicio
 * - setTo: function - Setter de fecha fin
 * - setLocalidad: function - Setter de localidad
 * - apply: function - Función que aplica filtros
 * - onClearFilters: function - Callback para limpiar filtros
 * - activeFiltersCount: number - Cantidad de filtros activos
 */
export function FilterDrawer({ 
  isOpen, 
  onClose, 
  from, 
  to, 
  localidad,
  setFrom,
  setTo,
  setLocalidad,
  apply,
  onClearFilters,
  activeFiltersCount 
}) {
  
  // Cerrar con ESC key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      // Prevenir scroll del body cuando drawer está abierto
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  return (
    <>
      {/* OVERLAY - Cerrar al click fuera */}
      <div 
        className={`
          fixed inset-0 bg-black/30 backdrop-blur-sm z-30 transition-opacity duration-300
          2xl:hidden
          ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}
        `}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* DRAWER - Slide down desde top */}
      <div 
        className={`
          fixed top-16 left-0 right-0 z-40
          bg-white dark:bg-slate-900 
          border-b border-gray-200 dark:border-slate-800
          shadow-2xl
          transition-transform duration-300 ease-in-out
          2xl:hidden
          ${isOpen ? 'translate-y-0' : '-translate-y-full'}
        `}
        role="dialog"
        aria-modal="true"
        aria-label="Panel de filtros"
      >
        <div className="max-w-7xl mx-auto px-4 xl:px-6 py-6">
          
          {/* Header del drawer */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <Filter className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Filtros Avanzados
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {activeFiltersCount > 0 
                    ? `${activeFiltersCount} filtro${activeFiltersCount > 1 ? 's' : ''} activo${activeFiltersCount > 1 ? 's' : ''}`
                    : 'Todos los datos'
                  }
                </p>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Cerrar filtros"
            >
              <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          {/* Grid de filtros */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            
            {/* Filtro 1: Moneda */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Moneda de Visualización
              </label>
              <MonedaToggle />
            </div>

            {/* Filtro 2: Rango de fechas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Período de Análisis
              </label>
              <DateRangePicker 
                from={from} 
                to={to} 
                onFrom={(d) => { setFrom(d); apply(); }} 
                onTo={(d) => { setTo(d); apply(); }}
                compact={false}
              />
            </div>

            {/* Filtro 3: Localidad */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Oficina
              </label>
              <LocalityFilter 
                value={localidad} 
                onChange={(v) => { setLocalidad(v); apply(); }}
                compact={false}
              />
            </div>
          </div>

          {/* Acciones del drawer */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-slate-800">
            <button
              onClick={onClearFilters}
              disabled={activeFiltersCount === 0}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Limpiar filtros
            </button>
            
            <button
              onClick={onClose}
              className="px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
            >
              Aplicar y cerrar
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

FilterDrawer.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  from: PropTypes.instanceOf(Date),
  to: PropTypes.instanceOf(Date),
  localidad: PropTypes.string,
  setFrom: PropTypes.func.isRequired,
  setTo: PropTypes.func.isRequired,
  setLocalidad: PropTypes.func.isRequired,
  apply: PropTypes.func.isRequired,
  onClearFilters: PropTypes.func.isRequired,
  activeFiltersCount: PropTypes.number
};

export default FilterDrawer;

