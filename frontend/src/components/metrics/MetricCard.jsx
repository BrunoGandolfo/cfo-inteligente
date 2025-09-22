import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import Card from '../ui/Card';

export function MetricCard({ title, value, icon: Icon, colorClass }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm text-gray-500 dark:text-slate-400">{title}</h3>
          {Icon && <Icon className={`w-5 h-5 ${colorClass}`} />}
        </div>
        <p className={`text-3xl font-bold ${colorClass}`}>{value}</p>
      </Card>
    </motion.div>
  );
}
MetricCard.propTypes = { title: PropTypes.string, value: PropTypes.node, icon: PropTypes.elementType, colorClass: PropTypes.string };
export default MetricCard;


