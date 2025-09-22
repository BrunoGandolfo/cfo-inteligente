import PropTypes from 'prop-types';
import { TrendingUp, TrendingDown, LineChart, ListOrdered } from 'lucide-react';
import MetricCard from './MetricCard';

export function MetricsGrid({ ingresosUYU, gastosUYU, margenOperativo, cantidadOperaciones, formatMoney }) {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 px-6">
      <MetricCard title="Ingresos del mes" value={formatMoney(ingresosUYU)} icon={TrendingUp} colorClass="text-emerald-600" />
      <MetricCard title="Gastos del mes" value={formatMoney(gastosUYU)} icon={TrendingDown} colorClass="text-coral-600" />
      <MetricCard title="Rentabilidad" value={`${margenOperativo}%`} icon={LineChart} colorClass="text-blue-600" />
      <MetricCard title="Operaciones" value={cantidadOperaciones} icon={ListOrdered} colorClass="text-gray-700 dark:text-slate-200" />
    </section>
  );
}
MetricsGrid.propTypes = {
  ingresosUYU: PropTypes.number,
  gastosUYU: PropTypes.number,
  margenOperativo: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  cantidadOperaciones: PropTypes.number,
  formatMoney: PropTypes.func
};
export default MetricsGrid;


