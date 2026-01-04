import { useState } from 'react';
import PropTypes from 'prop-types';
import { ThemeProvider } from '../../context/ThemeContext';
import { FilterProvider } from '../../context/FilterContext';
import Header from './Header';
import Sidebar from './Sidebar';
import ChatPanel from '../chat/ChatPanel';
import OperationsPanel from '../operations/OperationsPanel';
import MobileNav from './MobileNav';
import SoporteChat from '../soporte/SoporteChat';

export function Layout({ children }) {
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
              onChatToggle={() => setChatOpen(!chatOpen)}
              onOpsToggle={() => setOpsOpen(!opsOpen)}
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
            />
            {/* Chat de Soporte AI - botón flotante */}
            <SoporteChat />
          </div>
        </div>
      </FilterProvider>
    </ThemeProvider>
  );
}
Layout.propTypes = { children: PropTypes.node };
export default Layout;


