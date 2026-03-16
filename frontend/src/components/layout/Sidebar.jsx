import React, { useState } from 'react';
import { Home, FileText, Settings, Sparkles, Lock, Users, HelpCircle, BarChart3, Scale, Briefcase, Shield } from 'lucide-react';
import PropTypes from 'prop-types';
import clsx from 'clsx';
import ChangePasswordModal from '../auth/ChangePasswordModal';
import AdminUsersModal from '../admin/AdminUsersModal';

export function Sidebar({ active = 'Dashboard', onChatToggle, onOpsToggle, onSoporteToggle, onDashboardToggle, onIndicadoresToggle, onExpedientesToggle, onCasosToggle, onNotarialToggle, onALAToggle }) {
  // Solo estos 4 usuarios ven Expedientes y Casos (NO usar esSocio como criterio)
  const USUARIOS_ACCESO_EXPEDIENTES_CASOS = [
    "bgandolfo@cgmasociados.com",  // Bruno
    "gtaborda@grupoconexion.uy",   // Gonzalo
    "falgorta@grupoconexion.uy",   // Pancho
    "gferrari@grupoconexion.uy",   // Gerardo
  ];
  // Colaboradores con acceso completo al módulo ALA (igual que un socio)
  const USUARIOS_ACCESO_ALA = [
    "gferrari@grupoconexion.uy",   // Gerardo
  ];
  // Colaboradores con acceso al módulo Notarial (Contratos)
  const USUARIOS_ACCESO_NOTARIAL = [
    "gferrari@grupoconexion.uy",   // Gerardo
  ];
  // Colaboradores con acceso al módulo Operaciones (solo área Contable)
  const USUARIOS_ACCESO_OPERACIONES_CONTABLE = [
    "naraujo@grupoconexion.uy",    // Nicolás — solo área Contable
  ];
  
  // Verificar si el usuario es socio
  const esSocio = localStorage.getItem('esSocio') === 'true';
  const userEmail = localStorage.getItem('userEmail') || '';
  const veExpedientesYCasos = USUARIOS_ACCESO_EXPEDIENTES_CASOS.includes(userEmail.toLowerCase());
  const veALa = esSocio || USUARIOS_ACCESO_ALA.includes(userEmail.toLowerCase());
  const veNotarial = esSocio || USUARIOS_ACCESO_NOTARIAL.includes(userEmail.toLowerCase());
  const veOperacionesContable = USUARIOS_ACCESO_OPERACIONES_CONTABLE.includes(userEmail.toLowerCase());
  
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showAdminModal, setShowAdminModal] = useState(false);

  // Items completos para socios
  const allItems = [
    { key: 'Dashboard', icon: Home, label: 'Dashboard', action: onDashboardToggle },
    { key: 'Expedientes', icon: Scale, label: 'Expedientes', action: onExpedientesToggle },
    { key: 'Notarial', icon: FileText, label: 'Notarial', action: onNotarialToggle },
    { key: 'ALA', icon: Shield, label: 'ALA', action: onALAToggle },
    { key: 'Casos', icon: Briefcase, label: 'Casos', action: onCasosToggle },
    { key: 'Operaciones', icon: FileText, label: 'Operaciones', action: onOpsToggle },
    { key: 'CFO AI', icon: Sparkles, label: 'CFO AI', action: onChatToggle, highlight: true },
    { key: 'Indicadores', icon: BarChart3, label: 'Indicadores', action: onIndicadoresToggle },
    { key: 'Dudas', icon: HelpCircle, label: 'Dudas', action: onSoporteToggle },
    { key: 'Configuración', icon: Settings, label: 'Configuración' },
  ];

  // Lógica de filtrado de items según rol y permisos
  // CRÍTICO: Expedientes y Casos se muestran SOLO si el email está en USUARIOS_ACCESO_EXPEDIENTES_CASOS
  // NO usar esSocio como condición para estos dos ítems
  const items = esSocio
    ? allItems.filter(item => {
        // Expedientes y Casos: solo si está en la lista (NO por ser socio)
        if (item.key === 'Expedientes' || item.key === 'Casos') {
          return veExpedientesYCasos;
        }
        // ALA: si es socio o está en la lista
        if (item.key === 'ALA') {
          return veALa;
        }
        // Resto: visible para socios
        return true;
      })
    : (() => {
        const baseKeys = ['Dashboard', 'Dudas', 'Indicadores'];
        const extraKeys = [
          ...(veExpedientesYCasos ? ['Expedientes', 'Casos'] : []), 
          ...(veALa ? ['ALA'] : []),
          ...(veNotarial ? ['Notarial'] : []),
          ...(veOperacionesContable ? ['Operaciones'] : [])
        ];
        const visibleKeys = [...baseKeys, ...extraKeys];
        return allItems.filter(item => visibleKeys.includes(item.key));
      })();

  return (
    <aside className="hidden lg:flex lg:flex-col w-[250px] shrink-0 border-r border-border bg-surface pt-16 justify-between">
      <nav className="p-2 space-y-0.5">
        {items.map(({ key, icon: Icon, label, action, highlight }) => {
          const isActive = active === key;
          const isToolSection = key === 'CFO AI';
          return (
            <React.Fragment key={key}>
              {isToolSection ? (
                <div className="my-2 mx-4 border-t border-border" />
              ) : null}
              <button
                onClick={action}
                className={clsx(
                  'relative w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-accent-soft/70 text-accent'
                    : highlight
                    ? 'text-accent hover:bg-accent-soft/50 font-semibold'
                    : key === 'Indicadores'
                    ? 'text-orange-500 dark:text-orange-400 hover:bg-surface-alt/60'
                    : key === 'Dudas'
                    ? 'text-green-600 dark:text-green-400 hover:bg-surface-alt/60'
                    : 'text-text-secondary hover:bg-surface-alt/60'
                )}
              >
                {isActive ? (
                  <div className="absolute left-1 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-full bg-accent" />
                ) : null}
                <Icon className="w-5 h-5" />
                <span>{label}</span>
                {highlight ? (
                  <span className="ml-auto text-xs bg-accent-soft text-accent px-2 py-0.5 rounded-full">
                    Beta
                  </span>
                ) : null}
              </button>
            </React.Fragment>
          );
        })}
      </nav>
      
      {/* Botones de administración */}
      <div className="p-2 border-t border-border">
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
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-alt transition-colors"
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
  onALAToggle: PropTypes.func,
};
export default Sidebar;
