import PropTypes from 'prop-types';
import { LOCALIDADES } from '../../utils/constants';

export function LocalityFilter({ value, onChange, compact = false }) {
  
  // Clases base comunes
  const baseClasses = "border-2 border-blue-400 dark:border-blue-600 bg-white dark:bg-slate-900 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm hover:shadow-md cursor-pointer";
  
  // Clases específicas según modo
  const sizeClasses = compact
    ? "w-24 xl:w-32 px-2 py-1.5 text-xs xl:text-sm"
    : "w-32 px-3 py-2 text-sm";
  
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`${baseClasses} ${sizeClasses}`}
    >
      <option value="Todas">Todas</option>
      {LOCALIDADES.map(loc => <option key={loc} value={loc}>{loc}</option>)}
    </select>
  );
}
LocalityFilter.propTypes = { 
  value: PropTypes.string, 
  onChange: PropTypes.func,
  compact: PropTypes.bool
};
export default LocalityFilter;


