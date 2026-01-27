import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Soporte from './pages/Soporte';
import Indicadores from './pages/Indicadores';
import Expedientes from './pages/Expedientes';
import Contratos from './pages/Contratos';
import Casos from './pages/Casos';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import { Toaster } from 'react-hot-toast';
import WelcomeModal from './components/modals/WelcomeModal';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isValidating, setIsValidating] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);
  const [welcomeFrase, setWelcomeFrase] = useState(null);
  const [welcomeFraseLoading, setWelcomeFraseLoading] = useState(false);

  // Validar token contra el backend
  const validateToken = useCallback(async () => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      setIsValidating(false);
      return false;
    }

    try {
      // Verificar token con endpoint /me (accesible por todos los usuarios)
      await axios.get(`${import.meta.env.VITE_API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsValidating(false);
      
      // ELIMINADO: Ya no usamos localStorage para el modal
      
      return true;
    } catch {
      // Token inválido o expirado - limpiar
      localStorage.removeItem('token');
      localStorage.removeItem('userName');
      localStorage.removeItem('esSocio');
      localStorage.removeItem('userEmail');
      setIsValidating(false);
      return false;
    }
  }, []);

  // Callback centralizado para login exitoso
  const handleLoginSuccess = useCallback(() => {
    // Navegar inmediatamente
    setCurrentPage('dashboard');
    
    // Iniciar fetch de frase en paralelo (sin await, no bloquea)
    setWelcomeFraseLoading(true);
    
    fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/frases/motivacional`, {
      headers: { 
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    })
    .then(res => res.json())
    .then(data => {
      setWelcomeFrase(data.frase);
      setWelcomeFraseLoading(false);
    })
    .catch(() => {
      setWelcomeFrase('¡Bienvenido al sistema!');
      setWelcomeFraseLoading(false);
    });
    
    // Mostrar modal inmediatamente (mientras carga la frase)
    setShowWelcome(true);
  }, []);

  // Callback estable para cerrar modal
  const handleCloseWelcome = useCallback(() => {
    setShowWelcome(false);
    // Reset frase cuando se cierra el modal
    setWelcomeFrase(null);
    setWelcomeFraseLoading(false);
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      const isValid = await validateToken();
      if (isValid && (currentPage === 'home' || currentPage === 'login')) {
      setCurrentPage('dashboard');
      } else if (!isValid && !['home', 'login'].includes(currentPage)) {
      setCurrentPage('home');
    }
    };
    checkAuth();
  }, [currentPage, validateToken]);

  // Mostrar loading mientras valida
  if (isValidating) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Verificando sesión...</div>
      </div>
    );
  }

  if (currentPage === 'home') {
    return (
      <>
        <Home onLoginSuccess={handleLoginSuccess} />
        <Toaster position="top-right" />
      </>
    );
  }

  if (currentPage === 'login') {
    return (
      <>
        <Login onLoginSuccess={handleLoginSuccess} />
        <Toaster position="top-right" />
      </>
    );
  }

  const token = localStorage.getItem('token');
  if (!token) {
    return (
      <>
        <Home />
        <Toaster position="top-right" />
      </>
    );
  }

  // Función para renderizar el contenido según la página
  const renderContent = () => {
    switch (currentPage) {
      case 'expedientes':
        return <Expedientes />;
      case 'notarial':
        return <Contratos />;
      case 'casos':
        return <Casos />;
      case 'soporte':
        return <Soporte onNavigate={setCurrentPage} />;
      case 'indicadores':
        return <Indicadores onNavigate={setCurrentPage} />;
      case 'dashboard':
      default:
        return <Dashboard />;
    }
  };

  return (
    <>
      <Layout 
        onNavigate={setCurrentPage} 
        currentPage={currentPage}
        onNotarialToggle={() => setCurrentPage('notarial')}
        onCasosToggle={() => setCurrentPage('casos')}
      >
        {renderContent()}
      </Layout>
      <Toaster position="top-right" />
      <WelcomeModal 
        isOpen={showWelcome} 
        onClose={handleCloseWelcome}
        frasePreCargada={welcomeFrase}
        fraseLoading={welcomeFraseLoading}
      />
    </>
  );
}

export default App;
