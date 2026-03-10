import PropTypes from 'prop-types';
import clsx from 'clsx';

function getBadgeColor(tipo) {
  const t = (tipo || '').toUpperCase();
  switch (t) {
    case 'INGRESO':
      return 'bg-success/10 text-success';
    case 'GASTO':
      return 'bg-danger/10 text-danger';
    case 'RETIRO':
      return 'bg-retiro/10 text-retiro';
    case 'DISTRIBUCION':
    case 'DISTRIBUCIÓN':
      return 'bg-distribucion/10 text-distribucion';
    default:
      return 'bg-surface-alt text-text-secondary';
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


