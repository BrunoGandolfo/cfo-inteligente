import { Home, FileText, BarChart3, TrendingUp, Settings } from 'lucide-react';
import clsx from 'clsx';

export function Sidebar({ active = 'Dashboard' }) {
  const items = [
    { key: 'Dashboard', icon: Home, label: 'Dashboard' },
    { key: 'Operaciones', icon: FileText, label: 'Operaciones' },
    { key: 'Reportes', icon: BarChart3, label: 'Reportes' },
    { key: 'Análisis', icon: TrendingUp, label: 'Análisis' },
    { key: 'Configuración', icon: Settings, label: 'Configuración' },
  ];
  return (
    <aside className="hidden lg:flex lg:flex-col w-[250px] shrink-0 border-r bg-white dark:bg-slate-900 dark:border-slate-800 pt-16">
      <nav className="p-2 space-y-1">
        {items.map(({ key, icon: Icon, label }) => {
          const isActive = active === key;
          return (
            <button
              key={key}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-l-4 border-blue-600'
                  : 'text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800'
              )}
            >
              <Icon className="w-5 h-5" />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
export default Sidebar;


