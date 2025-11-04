import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

export function DateRangePicker({ from, to, onFrom, onTo, compact = false }) {
  
  // Clases base comunes
  const baseClasses = "border-2 border-blue-400 dark:border-blue-600 bg-white dark:bg-slate-900 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm hover:shadow-md";
  
  // Clases específicas según modo
  const sizeClasses = compact
    ? "w-28 xl:w-36 px-2 py-1.5 text-xs xl:text-sm"
    : "w-36 px-3 py-2 text-sm";
  
  return (
    <div className={`flex items-center ${compact ? 'gap-1 xl:gap-2' : 'gap-2'}`}>
      <DatePicker
        selected={from}
        onChange={onFrom}
        dateFormat="dd/MM/yyyy"
        className={`${baseClasses} ${sizeClasses}`}
        placeholderText="Desde"
      />
      <span className="text-gray-500 dark:text-gray-400 font-bold shrink-0">–</span>
      <DatePicker
        selected={to}
        onChange={onTo}
        dateFormat="dd/MM/yyyy"
        className={`${baseClasses} ${sizeClasses}`}
        placeholderText="Hasta"
      />
    </div>
  );
}
DateRangePicker.propTypes = { 
  from: PropTypes.instanceOf(Date), 
  to: PropTypes.instanceOf(Date), 
  onFrom: PropTypes.func, 
  onTo: PropTypes.func,
  compact: PropTypes.bool
};
export default DateRangePicker;


