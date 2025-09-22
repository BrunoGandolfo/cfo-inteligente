import PropTypes from 'prop-types';

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-lg shadow-sm ${className}`}>
      {children}
    </div>
  );
}
Card.propTypes = { children: PropTypes.node, className: PropTypes.string };
export default Card;


