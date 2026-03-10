import PropTypes from 'prop-types';

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-surface border border-border/70 rounded-xl shadow-none dark:shadow-none ${className}`}>
      {children}
    </div>
  );
}
Card.propTypes = { children: PropTypes.node, className: PropTypes.string };
export default Card;

