import PropTypes from 'prop-types';
import clsx from 'clsx';

export function Button({ children, variant = 'primary', className, ...props }) {
  const base = 'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variants = {
    primary: 'bg-accent hover:bg-accent-hover text-white focus:ring-accent',
    success: 'bg-success hover:bg-success/90 text-white focus:ring-success',
    danger: 'bg-danger hover:bg-danger/90 text-white focus:ring-danger',
    ghost: 'bg-surface hover:bg-surface-alt text-text-primary border border-border focus:ring-border-strong'
  };
  return (
    <button className={clsx(base, variants[variant], className)} {...props}>
      {children}
    </button>
  );
}
Button.propTypes = { children: PropTypes.node, variant: PropTypes.string, className: PropTypes.string };
export default Button;


