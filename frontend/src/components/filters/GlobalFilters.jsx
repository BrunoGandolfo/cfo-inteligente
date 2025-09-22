import { useFilters } from '../../hooks/useFilters';
import DateRangePicker from './DateRangePicker';
import LocalityFilter from './LocalityFilter';
import Button from '../ui/Button';

export function GlobalFilters() {
  const { from, to, setFrom, setTo, localidad, setLocalidad, apply } = useFilters();
  return (
    <div className="flex flex-wrap items-center gap-3">
      <DateRangePicker from={from} to={to} onFrom={setFrom} onTo={setTo} />
      <LocalityFilter value={localidad} onChange={setLocalidad} />
      <Button variant="primary" onClick={apply}>Aplicar filtros</Button>
    </div>
  );
}
export default GlobalFilters;


