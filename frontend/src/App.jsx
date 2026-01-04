import { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Soporte from './pages/Soporte';
import Indicadores from './pages/Indicadores';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import { Toaster } from 'react-hot-toast';

function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [isValidating, setIsValidating] = useState(true);

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
      return true;
    } catch (error) {
      // Token inválido o expirado - limpiar
      console.log('Token inválido, limpiando sesión...');
      localStorage.removeItem('token');
      localStorage.removeItem('userName');
      localStorage.removeItem('esSocio');
      setIsValidating(false);
      return false;
    }
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
        <Home />
        <Toaster position="top-right" />
      </>
    );
  }

  if (currentPage === 'login') {
    return (
      <>
        <Login onLoginSuccess={() => setCurrentPage('dashboard')} />
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
      <Layout onNavigate={setCurrentPage} currentPage={currentPage}>
        {renderContent()}
      </Layout>
      <Toaster position="top-right" />
    </>
  );
}

export default App;
