import PropTypes from 'prop-types';
import { Loader2, ArrowUpRight } from 'lucide-react';

/**
 * OperationButton - Botón de operación enterprise para Dashboard CFO
 * 
 * Patrón: Contextual Action Card (Stripe + Linear inspired)
 * Features: Multi-layer hover, micro-stats, keyboard shortcuts, badges
 * 
 * Props:
 * - variant: 'ingreso' | 'gasto' | 'retiro' | 'distribucion'
 * - title: Título del botón
 * - description: Descripción contextual
 * - lastActivity: Última operación (ej: "$1.234.567 - 2 Nov")
 * - shortcut: Keyboard shortcut (ej: "⌘ + 1")
 * - icon: Componente de icono (lucide-react)
 * - onClick: Handler del click
 * - loading: Estado de carga
 * - disabled: Estado deshabilitado
 */

// Configuración de variantes por tipo de operación
const VARIANTS = {
  ingreso: {
    color: 'emerald',
    badge: 'Frecuente',
    badgeBg: 'bg-emerald-100 dark:bg-emerald-900/30',
    badgeText: 'text-emerald-700 dark:text-emerald-300',
    borderBase: 'border-emerald-200/60 dark:border-emerald-700/40',
    borderHover: 'hover:border-emerald-500 dark:hover:border-emerald-600',
    shadow: 'hover:shadow-emerald-500/10',
    accentBar: 'from-emerald-500 to-emerald-600',
    iconBg: 'from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    statColor: 'text-emerald-600 dark:text-emerald-400',
    ring: 'focus:ring-emerald-500',
    spinnerColor: 'text-emerald-500'
  },
  gasto: {
    color: 'rose',
    badge: null,
    borderBase: 'border-rose-200/60 dark:border-rose-700/40',
    borderHover: 'hover:border-rose-500 dark:hover:border-rose-600',
    shadow: 'hover:shadow-rose-500/10',
    accentBar: 'from-rose-500 to-rose-600',
    iconBg: 'from-rose-50 to-rose-100 dark:from-rose-900/20 dark:to-rose-800/20',
    iconColor: 'text-rose-600 dark:text-rose-400',
    statColor: 'text-rose-600 dark:text-rose-400',
    ring: 'focus:ring-rose-500',
    spinnerColor: 'text-rose-500'
  },
  retiro: {
    color: 'amber',
    badge: 'Mensual',
    badgeBg: 'bg-amber-100 dark:bg-amber-900/30',
    badgeText: 'text-amber-700 dark:text-amber-300',
    borderBase: 'border-amber-200/60 dark:border-amber-700/40',
    borderHover: 'hover:border-amber-500 dark:hover:border-amber-600',
    shadow: 'hover:shadow-amber-500/10',
    accentBar: 'from-amber-500 to-amber-600',
    iconBg: 'from-amber-50 to-amber-100 dark:from-amber-900/20 dark:to-amber-800/20',
    iconColor: 'text-amber-600 dark:text-amber-400',
    statColor: 'text-amber-600 dark:text-amber-400',
    ring: 'focus:ring-amber-500',
    spinnerColor: 'text-amber-500'
  },
  distribucion: {
    color: 'blue',
    badge: 'Crítica',
    badgeBg: 'bg-blue-600 dark:bg-blue-500',
    badgeText: 'text-white',
    borderBase: 'border-blue-300 dark:border-blue-600',
    borderHover: 'hover:border-blue-500 dark:hover:border-blue-500',
    shadow: 'hover:shadow-blue-500/15',
    accentBar: 'from-blue-600 to-blue-700',
    iconBg: 'from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20',
    iconColor: 'text-blue-600 dark:text-blue-400',
    statColor: 'text-blue-700 dark:text-blue-400',
    ring: 'focus:ring-blue-500 ring-2 ring-blue-200/50 dark:ring-blue-800/40',
    spinnerColor: 'text-blue-600'
  }
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
  disabled = false
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
        bg-white dark:bg-slate-900
        border-2 ${config.borderBase} ${config.borderHover}
        rounded-xl
        p-5 xl:p-6
        hover:shadow-xl ${config.shadow}
        hover:-translate-y-0.5
        transition-all duration-200 ease-out
        focus:outline-none ${config.ring}
        disabled:opacity-50 disabled:cursor-not-allowed
        overflow-hidden
        text-left
        w-full
        ${variant === 'distribucion' ? config.ring : ''}
      `}
      aria-label={`${title} - ${description}`}
      aria-busy={loading}
    >
      {/* Accent bar (top) - aparece en hover */}
      <div className={`
        absolute top-0 left-0 right-0 h-1
        bg-gradient-to-r ${config.accentBar}
        opacity-0 group-hover:opacity-100
        transition-opacity duration-200
      `} />
      
      {/* Contenido principal */}
      <div className="relative flex items-start gap-4">
        
        {/* Icon container */}
        <div className={`
          flex-shrink-0
          w-12 h-12 xl:w-14 xl:h-14
          bg-gradient-to-br ${config.iconBg}
          rounded-lg
          flex items-center justify-center
          group-hover:scale-110 group-hover:rotate-3
          transition-transform duration-200
        `}>
          {loading ? (
            <Loader2 className={`w-6 h-6 xl:w-7 xl:h-7 ${config.spinnerColor} animate-spin`} />
          ) : (
            Icon && <Icon className={`w-6 h-6 xl:w-7 xl:h-7 ${config.iconColor}`} strokeWidth={2.5} />
          )}
        </div>
        
        {/* Content area */}
        <div className="flex-1 min-w-0">
          
          {/* Title + Badge */}
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h3 className="text-base xl:text-lg font-semibold text-gray-900 dark:text-white">
              {loading ? 'Procesando...' : title}
            </h3>
            {config.badge && !loading && (
              <span className={`
                hidden xl:inline-flex
                px-2 py-0.5
                text-[10px] font-bold uppercase tracking-wide
                ${config.badgeBg} ${config.badgeText}
                rounded-full
              `}>
                {config.badge}
              </span>
            )}
          </div>
          
          {/* Description */}
          <p className="text-xs xl:text-sm text-gray-600 dark:text-gray-400 mb-3 leading-relaxed line-clamp-2">
            {description}
          </p>
          
          {/* Stats line + Shortcut */}
          <div className="flex items-center justify-between gap-2">
            {/* Last activity stats */}
            {!loading && lastActivity && (
              <div className="flex items-center gap-2 text-xs">
                <span className={`font-medium ${config.statColor}`}>
                  {lastActivity.split(' - ')[0]}
                </span>
                {lastActivity.includes(' - ') && (
                  <>
                    <span className="text-gray-300 dark:text-slate-700">•</span>
                    <span className="text-gray-500 dark:text-gray-400">
                      {lastActivity.split(' - ')[1]}
                    </span>
                  </>
                )}
              </div>
            )}
            
            {/* Loading indicator (dots) */}
            {loading && (
              <div className="flex items-center gap-1.5">
                <div className={`w-1.5 h-1.5 ${config.iconColor.replace('text-', 'bg-')} rounded-full animate-pulse`}></div>
                <div className={`w-1.5 h-1.5 ${config.iconColor.replace('text-', 'bg-')} rounded-full animate-pulse animation-delay-100`}></div>
                <div className={`w-1.5 h-1.5 ${config.iconColor.replace('text-', 'bg-')} rounded-full animate-pulse animation-delay-200`}></div>
              </div>
            )}
            
            {/* Keyboard shortcut */}
            {shortcut && !loading && (
              <div className="hidden lg:flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-xs font-mono font-semibold text-gray-600 dark:text-gray-400">
                {shortcut}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Hover arrow indicator (top-right) */}
      <div className={`
        absolute top-4 right-4
        opacity-0 group-hover:opacity-100
        translate-x-1 group-hover:translate-x-0
        transition-all duration-200
      `}>
        <ArrowUpRight className={`w-4 h-4 ${config.iconColor}`} strokeWidth={2.5} />
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
  disabled: PropTypes.bool
};

export default OperationButton;

