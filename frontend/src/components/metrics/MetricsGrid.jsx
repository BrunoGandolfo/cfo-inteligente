import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, LineChart, Trophy } from 'lucide-react';
import MetricCard from './MetricCard';

export function MetricsGrid({ ingresos, gastos, margenOperativo, areaLider }) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 px-6">
      <MetricCard title="Ingresos del mes" value={ingresos} icon={TrendingUp} colorClass="text-emerald-600" />
      <MetricCard title="Gastos del mes" value={gastos} icon={TrendingDown} colorClass="text-coral-600" />
      <MetricCard title="Rentabilidad" value={`${margenOperativo}%`} icon={LineChart} colorClass="text-blue-600" />
      <MetricCard title="Área líder" value={areaLider?.nombre || '—'} icon={Trophy} colorClass="text-gray-700 dark:text-slate-200" />
    </section>
  );
}
MetricsGrid.propTypes = {
  ingresos: PropTypes.string,
  gastos: PropTypes.string,
  margenOperativo: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  areaLider: PropTypes.object,
};
export default MetricsGrid;


