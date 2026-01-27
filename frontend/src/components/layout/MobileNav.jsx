import { useState } from 'react';
import { X, Home, FileText, Sparkles, Lock, Users, LogOut, HelpCircle, BarChart3, Scale, Briefcase } from 'lucide-react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import ChangePasswordModal from '../auth/ChangePasswordModal';
import AdminUsersModal from '../admin/AdminUsersModal';
import toast from 'react-hot-toast';

export function MobileNav({ isOpen, onClose, onChatToggle, onOpsToggle, onSoporteToggle, onIndicadoresToggle, onExpedientesToggle, onCasosToggle, onNotarialToggle, onDashboardToggle }) {
  // Solo estos usuarios ven Expedientes y Casos (socios ya no tienen acceso automático)
  const USUARIOS_ACCESO_EXPEDIENTES_CASOS = [
    "gferrari@grupoconexion.uy",  // Gerardo
    "falgorta@grupoconexion.uy",   // Pancho
    "gtaborda@grupoconexion.uy",   // Gonzalo
  ];
  
  const esSocio = localStorage.getItem('esSocio') === 'true';
  const userName = localStorage.getItem('userName') || 'Usuario';
  const userEmail = localStorage.getItem('userEmail') || '';
  const veExpedientesYCasos = USUARIOS_ACCESO_EXPEDIENTES_CASOS.includes(userEmail.toLowerCase());
  
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);

  // Items del menú (sincronizado con Sidebar)
  const allItems = [
    { key: 'Dashboard', icon: Home, label: 'Dashboard', action: () => { onDashboardToggle?.(); onClose(); } },
    { key: 'Expedientes', icon: Scale, label: 'Expedientes', action: () => { onExpedientesToggle?.(); onClose(); } },
    { key: 'Notarial', icon: FileText, label: 'Notarial', action: () => { onNotarialToggle?.(); onClose(); } },
    { key: 'Casos', icon: Briefcase, label: 'Casos', action: () => { onCasosToggle?.(); onClose(); } },
    { key: 'Operaciones', icon: FileText, label: 'Operaciones', action: () => { onOpsToggle?.(); onClose(); } },
    { key: 'CFO AI', icon: Sparkles, label: 'CFO AI', action: () => { onChatToggle?.(); onClose(); }, highlight: true },
    { key: 'Indicadores', icon: BarChart3, label: 'Indicadores', action: () => { onIndicadoresToggle?.(); onClose(); }, indicadorItem: true },
    { key: 'Soporte', icon: HelpCircle, label: 'Soporte', action: () => { onSoporteToggle?.(); onClose(); }, supportItem: true },
  ];

  // Lógica de filtrado de items según rol y permisos
  const items = esSocio
    ? allItems.filter(item => (item.key === 'Expedientes' || item.key === 'Casos') ? veExpedientesYCasos : true)
    : veExpedientesYCasos
    ? allItems.filter(item => ['Dashboard', 'Soporte', 'Indicadores', 'Expedientes', 'Casos'].includes(item.key))
    : allItems.filter(item => ['Dashboard', 'Soporte', 'Indicadores'].includes(item.key));

  const handleLogout = () => {
    toast.success('Sesión cerrada correctamente');
    setTimeout(() => {
      localStorage.clear();
      window.location.href = '/login';
    }, 500);
  };

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black/50 z-50 lg:hidden"
            />

            {/* Drawer */}
            <motion.aside
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 h-full w-[280px] bg-white dark:bg-slate-900 border-r border-gray-200 dark:border-slate-800 z-50 flex flex-col lg:hidden"
            >
              {/* Header del drawer */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-slate-800">
                <div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">Menú</h2>
                  <p className="text-sm text-gray-500 dark:text-slate-400">{userName}</p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-800"
                  aria-label="Cerrar menú"
                >
                  <X className="w-5 h-5 text-gray-600 dark:text-slate-400" />
                </button>
              </div>

              {/* Navegación principal */}
              <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                {items.map(({ key, icon: Icon, label, action, highlight, supportItem, indicadorItem }) => (
                  <button
                    key={key}
                    onClick={action}
                    className={clsx(
                      'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                      highlight
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 font-semibold'
                        : indicadorItem
                        ? 'text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20'
                        : supportItem
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
                ))}
              </nav>

              {/* Sección inferior */}
              <div className="p-3 border-t border-gray-200 dark:border-slate-700 space-y-1">
                {/* Administrar usuarios - solo socios */}
                {esSocio && (
                  <button
                    onClick={() => setShowAdminModal(true)}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20"
                  >
                    <Users className="w-5 h-5" />
                    <span>Administrar usuarios</span>
                  </button>
                )}

                {/* Cambiar contraseña */}
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-gray-600 dark:text-slate-400 hover:bg-gray-50 dark:hover:bg-slate-800"
                >
                  <Lock className="w-5 h-5" />
                  <span>Cambiar contraseña</span>
                </button>

                {/* Cerrar sesión */}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Cerrar sesión</span>
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Modales (fuera del AnimatePresence para que funcionen) */}
      <ChangePasswordModal 
        isOpen={showPasswordModal} 
        onClose={() => setShowPasswordModal(false)} 
      />
      <AdminUsersModal
        isOpen={showAdminModal}
        onClose={() => setShowAdminModal(false)}
      />
    </>
  );
}

MobileNav.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onChatToggle: PropTypes.func,
  onOpsToggle: PropTypes.func,
  onSoporteToggle: PropTypes.func,
  onIndicadoresToggle: PropTypes.func,
  onExpedientesToggle: PropTypes.func,
  onCasosToggle: PropTypes.func,
  onNotarialToggle: PropTypes.func,
  onDashboardToggle: PropTypes.func,
};

export default MobileNav;
