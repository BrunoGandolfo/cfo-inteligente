import { Home, Bot, FileText, ChevronDown, Download, BarChart4, Settings, BookOpen } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

export function Sidebar() {
  const [openReports, setOpenReports] = useState(true);
  return (
    <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 border-r bg-white dark:bg-slate-900 dark:border-slate-800 pt-20">
      <nav className="p-4 space-y-2">
        <NavItem icon={Home} label="Dashboard" />
        <NavItem icon={Bot} label="Chat CFO" />
        <div>
          <NavItem icon={FileText} label="Reportes" actionIcon={ChevronDown} onAction={() => setOpenReports(v => !v)} />
          <div className={clsx('ml-9 mt-2 space-y-1', { hidden: !openReports })}>
            <SubItem label="Por área" />
            <SubItem label="Por socio" />
            <SubItem label="Rentabilidad" />
          </div>
        </div>
        <NavItem icon={Download} label="Exportar" />
        <NavItem icon={BarChart4} label="Analytics" />
        <NavItem icon={Settings} label="Configuración" />
        <NavItem icon={BookOpen} label="Ayuda/Documentación" />
      </nav>
    </aside>
  );
}

function NavItem({ icon: Icon, label, actionIcon: ActionIcon, onAction }) {
  return (
    <div className="flex items-center justify-between">
      <button className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-gray-700 dark:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800">
        <Icon className="w-5 h-5 text-gray-600 dark:text-slate-300" />
        {label}
      </button>
      {ActionIcon && <button onClick={onAction} className="px-2"><ActionIcon className="w-4 h-4 text-gray-500" /></button>}
    </div>
  );
}
function SubItem({ label }) {
  return <button className="w-full text-left px-3 py-1.5 rounded-md text-sm text-gray-600 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800">{label}</button>;
}
export default Sidebar;


