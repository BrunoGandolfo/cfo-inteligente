import { useState } from 'react';
import { Home, FileText, Settings, Sparkles, Lock, Users, HelpCircle, BarChart3, Scale, Briefcase } from 'lucide-react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import ChangePasswordModal from '../auth/ChangePasswordModal';
import AdminUsersModal from '../admin/AdminUsersModal';

export function Sidebar({ active = 'Dashboard', onChatToggle, onOpsToggle, onSoporteToggle, onDashboardToggle, onIndicadoresToggle, onExpedientesToggle, onCasosToggle, onNotarialToggle }) {
  // Verificar si el usuario es socio
  const esSocio = localStorage.getItem('esSocio') === 'true';
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);

  // Items completos para socios
  const allItems = [
    { key: 'Dashboard', icon: Home, label: 'Dashboard', action: onDashboardToggle },
    { key: 'Expedientes', icon: Scale, label: 'Expedientes', action: onExpedientesToggle },
    { key: 'Notarial', icon: FileText, label: 'Notarial', action: onNotarialToggle },
    { key: 'Casos', icon: Briefcase, label: 'Casos', action: onCasosToggle },
    { key: 'Operaciones', icon: FileText, label: 'Operaciones', action: onOpsToggle },
    { key: 'CFO AI', icon: Sparkles, label: 'CFO AI', action: onChatToggle, highlight: true },
    { key: 'Indicadores', icon: BarChart3, label: 'Indicadores', action: onIndicadoresToggle },
    { key: 'Soporte', icon: HelpCircle, label: 'Soporte', action: onSoporteToggle },
    { key: 'Configuración', icon: Settings, label: 'Configuración' },
  ];

  // Colaboradores solo ven Dashboard y Soporte
  const items = esSocio 
    ? allItems 
    : allItems.filter(item => ['Dashboard', 'Soporte'].includes(item.key));

  return (
    <aside className="hidden lg:flex lg:flex-col w-[250px] shrink-0 border-r bg-white dark:bg-slate-900 dark:border-slate-800 pt-16 justify-between">
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
                  : key === 'Indicadores'
                  ? 'text-orange-500 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20'
                  : key === 'Soporte'
                  ? 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
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
      
      {/* Botones de administración */}
      <div className="p-2 border-t border-gray-200 dark:border-slate-700">
        {/* Administrar usuarios - solo socios */}
        {esSocio && (
          <button
            onClick={() => setShowAdminModal(true)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors mb-1"
          >
            <Users className="w-5 h-5" />
            <span>Administrar usuarios</span>
          </button>
        )}
        
        {/* Cambiar Contraseña - visible para todos */}
        <button
          onClick={() => setShowPasswordModal(true)}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
        >
          <Lock className="w-5 h-5" />
          <span>Cambiar contraseña</span>
        </button>
      </div>
      
      {/* Modal de cambio de contraseña */}
      <ChangePasswordModal 
        isOpen={showPasswordModal} 
        onClose={() => setShowPasswordModal(false)} 
      />
      
      {/* Modal de administración de usuarios */}
      <AdminUsersModal
        isOpen={showAdminModal}
        onClose={() => setShowAdminModal(false)}
      />
    </aside>
  );
}
Sidebar.propTypes = {
  active: PropTypes.string,
  onChatToggle: PropTypes.func,
  onOpsToggle: PropTypes.func,
  onSoporteToggle: PropTypes.func,
  onDashboardToggle: PropTypes.func,
  onIndicadoresToggle: PropTypes.func,
  onExpedientesToggle: PropTypes.func,
  onCasosToggle: PropTypes.func,
  onNotarialToggle: PropTypes.func,
};
export default Sidebar;
