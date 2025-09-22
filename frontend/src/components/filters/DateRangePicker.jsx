import PropTypes from 'prop-types';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

export function DateRangePicker({ from, to, onFrom, onTo }) {
  return (
    <div className="flex items-center gap-2">
      <DatePicker selected={from} onChange={onFrom} dateFormat="dd/MM/yyyy" className="px-3 py-2 border rounded-md" />
      <span className="text-gray-500">–</span>
      <DatePicker selected={to} onChange={onTo} dateFormat="dd/MM/yyyy" className="px-3 py-2 border rounded-md" />
    </div>
  );
}
DateRangePicker.propTypes = { from: PropTypes.instanceOf(Date), to: PropTypes.instanceOf(Date), onFrom: PropTypes.func, onTo: PropTypes.func };
export default DateRangePicker;


