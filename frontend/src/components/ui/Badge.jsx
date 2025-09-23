import PropTypes from 'prop-types';
import clsx from 'clsx';

function getBadgeColor(tipo) {
  const t = (tipo || '').toUpperCase();
  switch (t) {
    case 'INGRESO':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
    case 'GASTO':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-300';
    case 'RETIRO':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
    case 'DISTRIBUCION':
    case 'DISTRIBUCIÓN':
      return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-slate-200';
  }
}

export function Badge({ tipo }) {
  const color = getBadgeColor(tipo);
  return (
    <span className={clsx('px-2 py-1 text-xs font-semibold rounded-full', color)}>
      {(tipo || '').toUpperCase()}
    </span>
  );
}
Badge.propTypes = { tipo: PropTypes.string };
export default Badge;


