import PropTypes from 'prop-types';
import clsx from 'clsx';

export function Button({ children, variant = 'primary', className, ...props }) {
  const base = 'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
    success: 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500',
    danger: 'bg-coral-600 hover:bg-coral-700 text-white focus:ring-coral-500',
    ghost: 'bg-white hover:bg-gray-50 text-gray-900 border border-gray-300 focus:ring-gray-400'
  };
  return (
    <button className={clsx(base, variants[variant], className)} {...props}>
      {children}
    </button>
  );
}
Button.propTypes = { children: PropTypes.node, variant: PropTypes.string, className: PropTypes.string };
export default Button;


