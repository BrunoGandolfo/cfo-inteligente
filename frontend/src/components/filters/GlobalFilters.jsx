import { useFilters } from '../../hooks/useFilters';
import DateRangePicker from './DateRangePicker';
import LocalityFilter from './LocalityFilter';

export function GlobalFilters() {
  const { from, to, setFrom, setTo, localidad, setLocalidad, apply } = useFilters();

  const handleDateChange = (setter) => (value) => {
    setter(value);
    apply();
  };

  const handleLocalityChange = (value) => {
    setLocalidad(value);
    apply();
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <DateRangePicker 
        from={from} 
        to={to} 
        onFrom={handleDateChange(setFrom)} 
        onTo={handleDateChange(setTo)} 
      />
      <LocalityFilter 
        value={localidad} 
        onChange={handleLocalityChange} 
      />
    </div>
  );
}
export default GlobalFilters;


