import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, LineChart, Trophy } from 'lucide-react';
import MetricCard from './MetricCard';

export function MetricsGrid({ ingresos, gastos, margenOperativo, areaLider }) {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 xl:gap-6 mb-8 px-4 xl:px-6">
      <div className="rounded-lg shadow-sm hover:shadow-md transform hover:scale-[1.02] transition-all duration-200 border-l-4 border-green-500 bg-white dark:bg-slate-900">
        <MetricCard title="Ingresos del mes" value={ingresos} icon={TrendingUp} colorClass="text-emerald-600" />
      </div>
      <div className="rounded-lg shadow-sm hover:shadow-md transform hover:scale-[1.02] transition-all duration-200 border-l-4 border-red-500 bg-white dark:bg-slate-900">
        <MetricCard title="Gastos del mes" value={gastos} icon={TrendingDown} colorClass="text-coral-600" />
      </div>
      <div className="rounded-lg shadow-sm hover:shadow-md transform hover:scale-[1.02] transition-all duration-200 border-l-4 border-blue-500 bg-white dark:bg-slate-900">
        <MetricCard title="Rentabilidad" value={`${margenOperativo}%`} icon={LineChart} colorClass="text-blue-600" />
      </div>
      <div className="rounded-lg shadow-sm hover:shadow-md transform hover:scale-[1.02] transition-all duration-200 border-l-4 border-purple-500 bg-white dark:bg-slate-900">
        <MetricCard title="Área líder" value={areaLider?.nombre || '—'} icon={Trophy} colorClass="text-gray-700 dark:text-slate-200" />
      </div>
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


