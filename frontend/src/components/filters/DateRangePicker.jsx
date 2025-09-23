import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

export function DateRangePicker({ from, to, onFrom, onTo }) {
  return (
    <div className="flex items-center gap-2">
      <DatePicker
        selected={from}
        onChange={onFrom}
        dateFormat="dd/MM/yyyy"
        className="px-3 py-2 text-sm border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
      />
      <span className="text-gray-500">–</span>
      <DatePicker
        selected={to}
        onChange={onTo}
        dateFormat="dd/MM/yyyy"
        className="px-3 py-2 text-sm border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-gray-900 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
      />
    </div>
  );
}
DateRangePicker.propTypes = { from: PropTypes.instanceOf(Date), to: PropTypes.instanceOf(Date), onFrom: PropTypes.func, onTo: PropTypes.func };
export default DateRangePicker;


