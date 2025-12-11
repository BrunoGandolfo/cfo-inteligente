import { Home, FileText, BarChart3, TrendingUp, Settings, Sparkles } from 'lucide-react';
import PropTypes from 'prop-types';
import clsx from 'clsx';

export function Sidebar({ active = 'Dashboard', onChatToggle, onOpsToggle, onReportsToggle }) {
  // Verificar si el usuario es socio
  const esSocio = localStorage.getItem('esSocio') === 'true';

  // Items completos para socios
  const allItems = [
    { key: 'Dashboard', icon: Home, label: 'Dashboard' },
    { key: 'Operaciones', icon: FileText, label: 'Operaciones', action: onOpsToggle },
    { key: 'Reportes', icon: BarChart3, label: 'Reportes', action: onReportsToggle },
    { key: 'Análisis', icon: TrendingUp, label: 'Análisis' },
    { key: 'CFO AI', icon: Sparkles, label: 'CFO AI', action: onChatToggle, highlight: true },
    { key: 'Configuración', icon: Settings, label: 'Configuración' },
  ];

  // Colaboradores solo ven Dashboard
  const items = esSocio 
    ? allItems 
    : allItems.filter(item => item.key === 'Dashboard');

  return (
    <aside className="hidden lg:flex lg:flex-col w-[250px] shrink-0 border-r bg-white dark:bg-slate-900 dark:border-slate-800 pt-16">
      <nav className="p-2 space-y-1">
        {items.map(({ key, icon: Icon, label, action, highlight }) => {
          const isActive = active === key;
          return (
            <button
              key={key}
              onClick={action}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-l-4 border-blue-600'
                  : highlight
                  ? 'text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 font-semibold'
                  : 'text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800'
              )}
            >
              <Icon className={clsx('w-5 h-5', highlight && 'animate-pulse')} />
              <span>{label}</span>
              {highlight && (
                <span className="ml-auto text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
                  Beta
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
Sidebar.propTypes = {
  active: PropTypes.string,
  onChatToggle: PropTypes.func,
  onOpsToggle: PropTypes.func,
  onReportsToggle: PropTypes.func
};
export default Sidebar;
