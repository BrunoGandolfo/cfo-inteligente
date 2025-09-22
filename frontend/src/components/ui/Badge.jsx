import PropTypes from 'prop-types';
import clsx from 'clsx';
import { TIPO_CONFIG } from '../../utils/constants';

export function Badge({ tipo }) {
  const cfg = TIPO_CONFIG?.[(tipo || '').toUpperCase()] || 'bg-gray-100 text-gray-700 border-gray-200';
  return (
    <span className={clsx('px-2 py-1 text-xs font-semibold rounded-full border', cfg)}>
      {(tipo || '').toUpperCase()}
    </span>
  );
}
Badge.propTypes = { tipo: PropTypes.string };
export default Badge;


