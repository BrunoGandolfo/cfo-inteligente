/**
 * Card para mostrar un indicador económico individual.
 * 
 * Sigue el patrón de MetricCard.jsx con border-l-4 de color.
 */

import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import Card from '../ui/Card';

export function IndicadorCard({ titulo, valor, subtitulo, icono: Icon, colorBorde, colorIcono }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 ${colorBorde} bg-white dark:bg-slate-900`}
    >
      <Card className="p-5 border-0 shadow-none bg-transparent">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-sm font-medium text-gray-500 dark:text-slate-400 mb-1">
              {titulo}
            </h3>
            <p className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">
              {valor}
            </p>
            {subtitulo && (
              <p className="text-xs text-gray-400 dark:text-slate-500 mt-1">
                {subtitulo}
              </p>
            )}
          </div>
          {Icon && (
            <div className={`p-2 rounded-lg bg-gray-50 dark:bg-slate-800 ${colorIcono}`}>
              <Icon className="w-5 h-5" />
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

IndicadorCard.propTypes = {
  titulo: PropTypes.string.isRequired,
  valor: PropTypes.string.isRequired,
  subtitulo: PropTypes.string,
  icono: PropTypes.elementType,
  colorBorde: PropTypes.string,
  colorIcono: PropTypes.string,
};

IndicadorCard.defaultProps = {
  colorBorde: 'border-blue-500',
  colorIcono: 'text-blue-500',
};

export default IndicadorCard;
