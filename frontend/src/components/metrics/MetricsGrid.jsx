import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, LineChart, Trophy } from 'lucide-react';
import MetricCard from './MetricCard';

export function MetricsGrid({ ingresos, gastos, margenOperativo, areaLider }) {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 xl:gap-5 mb-8 px-4 xl:px-6">
      <MetricCard
        title="Ingresos del mes"
        value={ingresos}
        icon={TrendingUp}
        colorClass="text-emerald-600 dark:text-emerald-400"
        iconBgClass="bg-emerald-500/10"
      />
      <MetricCard
        title="Gastos del mes"
        value={gastos}
        icon={TrendingDown}
        colorClass="text-rose-600 dark:text-rose-400"
        iconBgClass="bg-rose-500/10"
      />
      <MetricCard
        title="Rentabilidad"
        value={`${margenOperativo}%`}
        icon={LineChart}
        colorClass="text-blue-600 dark:text-blue-400"
        iconBgClass="bg-blue-500/10"
      />
      <MetricCard
        title="Area lider"
        value={areaLider || '\u2014'}
        icon={Trophy}
        colorClass="text-amber-600 dark:text-amber-400"
        iconBgClass="bg-amber-500/10"
      />
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
