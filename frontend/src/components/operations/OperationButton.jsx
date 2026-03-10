import PropTypes from 'prop-types';
import { Loader2 } from 'lucide-react';

/**
 * OperationButton - Botón de operación para Dashboard CFO
 * Diseño limpio: ícono con fondo suave + título + descripción + shortcut
 */

const VARIANTS = {
  ingreso: {
    iconBg: 'bg-emerald-500/10',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    borderHover: 'hover:border-emerald-500/50',
    ring: 'focus:ring-emerald-500/30',
    statColor: 'text-emerald-600 dark:text-emerald-400',
    spinnerColor: 'text-emerald-500',
  },
  gasto: {
    iconBg: 'bg-rose-500/10',
    iconColor: 'text-rose-600 dark:text-rose-400',
    borderHover: 'hover:border-rose-500/50',
    ring: 'focus:ring-rose-500/30',
    statColor: 'text-rose-600 dark:text-rose-400',
    spinnerColor: 'text-rose-500',
  },
  retiro: {
    iconBg: 'bg-amber-500/10',
    iconColor: 'text-amber-600 dark:text-amber-400',
    borderHover: 'hover:border-amber-500/50',
    ring: 'focus:ring-amber-500/30',
    statColor: 'text-amber-600 dark:text-amber-400',
    spinnerColor: 'text-amber-500',
  },
  distribucion: {
    iconBg: 'bg-blue-500/10',
    iconColor: 'text-blue-600 dark:text-blue-400',
    borderHover: 'hover:border-blue-500/50',
    ring: 'focus:ring-blue-500/30',
    statColor: 'text-blue-600 dark:text-blue-400',
    spinnerColor: 'text-blue-500',
  },
};

export function OperationButton({
  variant = 'ingreso',
  title,
  description,
  lastActivity,
  shortcut,
  icon: Icon,
  onClick,
  loading = false,
  disabled = false,
}) {
  const config = VARIANTS[variant];

  if (!config) {
    console.error(`Invalid variant: ${variant}`);
    return null;
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        group relative
        bg-surface
        border border-border ${config.borderHover}
        rounded-xl
        p-5
        hover:shadow-lg
        transition-all duration-200
        focus:outline-none focus:ring-2 ${config.ring}
        disabled:opacity-50 disabled:cursor-not-allowed
        text-left
        w-full
      `}
      aria-label={`${title} - ${description}`}
      aria-busy={loading}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div
          className={`
          flex-shrink-0
          w-11 h-11
          ${config.iconBg}
          rounded-xl
          flex items-center justify-center
        `}
        >
          {loading ? (
            <Loader2 className={`w-5 h-5 ${config.spinnerColor} animate-spin`} />
          ) : (
            Icon && <Icon className={`w-5 h-5 ${config.iconColor}`} strokeWidth={2} />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-text-primary mb-0.5">
            {loading ? 'Procesando...' : title}
          </h3>
          <p className="text-xs text-text-secondary leading-relaxed line-clamp-2 mb-3">
            {description}
          </p>

          {/* Bottom row: last activity + shortcut */}
          <div className="flex items-center justify-between gap-2">
            {!loading && lastActivity ? (
              <div className="flex items-center gap-1.5 text-xs">
                <span className={`font-medium tabular-nums ${config.statColor}`}>
                  {lastActivity.split(' - ')[0]}
                </span>
                {lastActivity.includes(' - ') ? (
                  <>
                    <span className="text-text-muted">·</span>
                    <span className="text-text-secondary">{lastActivity.split(' - ')[1]}</span>
                  </>
                ) : null}
              </div>
            ) : null}

            {loading ? (
              <div className="flex items-center gap-1">
                <div className={`w-1 h-1 rounded-full ${config.iconBg.replace('bg-', 'bg-').replace('/10', '')} animate-pulse`} />
                <div className={`w-1 h-1 rounded-full ${config.iconBg.replace('bg-', 'bg-').replace('/10', '')} animate-pulse`} style={{ animationDelay: '150ms' }} />
                <div className={`w-1 h-1 rounded-full ${config.iconBg.replace('bg-', 'bg-').replace('/10', '')} animate-pulse`} style={{ animationDelay: '300ms' }} />
              </div>
            ) : null}

            {shortcut && !loading ? (
              <kbd className="hidden lg:inline-flex px-1.5 py-0.5 bg-surface-alt border border-border rounded text-[10px] font-mono text-text-muted">
                {shortcut}
              </kbd>
            ) : null}
          </div>
        </div>
      </div>
    </button>
  );
}

OperationButton.propTypes = {
  variant: PropTypes.oneOf(['ingreso', 'gasto', 'retiro', 'distribucion']).isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  lastActivity: PropTypes.string,
  shortcut: PropTypes.string,
  icon: PropTypes.elementType.isRequired,
  onClick: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  disabled: PropTypes.bool,
};

export default OperationButton;
