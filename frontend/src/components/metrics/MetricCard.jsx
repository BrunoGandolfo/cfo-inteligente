import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import Card from '../ui/Card';

export function MetricCard({ title, value, icon: Icon, colorClass, iconBgClass }) {
  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="p-5 xl:p-6">
        <div className="flex items-start gap-4">
          {Icon ? (
            <div className={`flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center ${iconBgClass || 'bg-surface-alt'}`}>
              <Icon className={`w-5 h-5 ${colorClass}`} strokeWidth={2} />
            </div>
          ) : null}
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text-secondary mb-1 truncate">{title}</p>
            <p className="text-2xl xl:text-3xl font-semibold tabular-nums tracking-tight text-text-primary">
              {value}
            </p>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
MetricCard.propTypes = {
  title: PropTypes.string,
  value: PropTypes.node,
  icon: PropTypes.elementType,
  colorClass: PropTypes.string,
  iconBgClass: PropTypes.string,
};
export default MetricCard;
