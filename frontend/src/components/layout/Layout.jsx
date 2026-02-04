import { useState } from 'react';
import PropTypes from 'prop-types';
import { ThemeProvider } from '../../context/ThemeContext';
import { FilterProvider } from '../../context/FilterContext';
import Header from './Header';
import Sidebar from './Sidebar';
import ChatPanel from '../chat/ChatPanel';
import OperationsPanel from '../operations/OperationsPanel';
import MobileNav from './MobileNav';

export function Layout({ children, onNavigate, currentPage, onCasosToggle, onNotarialToggle, onALAToggle }) {
  const [chatOpen, setChatOpen] = useState(false);
  const [opsOpen, setOpsOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <ThemeProvider>
      <FilterProvider>
        <div className="min-h-screen bg-gray-50 dark:bg-slate-950">
          <Header onMobileMenuToggle={() => setMobileNavOpen(true)} />
          <div className="pt-20 flex">
            <Sidebar 
              active={
                currentPage === 'soporte' ? 'Dudas' :
                currentPage === 'indicadores' ? 'Indicadores' :
                currentPage === 'notarial' ? 'Notarial' :
                currentPage === 'ala' ? 'ALA' :
                currentPage === 'expedientes' ? 'Expedientes' :
                currentPage === 'casos' ? 'Casos' :
                'Dashboard'
              }
              onChatToggle={() => setChatOpen(!chatOpen)}
              onOpsToggle={() => setOpsOpen(!opsOpen)}
              onSoporteToggle={() => onNavigate?.('soporte')}
              onDashboardToggle={() => onNavigate?.('dashboard')}
              onIndicadoresToggle={() => onNavigate?.('indicadores')}
              onExpedientesToggle={() => onNavigate?.('expedientes')}
              onCasosToggle={onCasosToggle}
              onNotarialToggle={onNotarialToggle}
              onALAToggle={onALAToggle}
            />
            <main className="flex-1 p-4 lg:p-6 overflow-y-auto">{children}</main>
            <ChatPanel isOpen={chatOpen} onClose={() => setChatOpen(false)} />
            <OperationsPanel 
              isOpen={opsOpen} 
              onClose={() => setOpsOpen(false)}
            />
            <MobileNav
              isOpen={mobileNavOpen}
              onClose={() => setMobileNavOpen(false)}
              onChatToggle={() => setChatOpen(!chatOpen)}
              onOpsToggle={() => setOpsOpen(!opsOpen)}
              onSoporteToggle={() => { setMobileNavOpen(false); onNavigate?.('soporte'); }}
              onIndicadoresToggle={() => { setMobileNavOpen(false); onNavigate?.('indicadores'); }}
              onExpedientesToggle={() => { setMobileNavOpen(false); onNavigate?.('expedientes'); }}
              onCasosToggle={() => { setMobileNavOpen(false); onCasosToggle?.(); }}
              onNotarialToggle={() => { setMobileNavOpen(false); onNotarialToggle?.(); }}
              onALAToggle={() => { setMobileNavOpen(false); onALAToggle?.(); }}
              onDashboardToggle={() => { setMobileNavOpen(false); onNavigate?.('dashboard'); }}
            />
          </div>
        </div>
      </FilterProvider>
    </ThemeProvider>
  );
}
Layout.propTypes = { 
  children: PropTypes.node,
  onNavigate: PropTypes.func,
  currentPage: PropTypes.string,
  onCasosToggle: PropTypes.func,
  onNotarialToggle: PropTypes.func,
  onALAToggle: PropTypes.func
};
export default Layout;
