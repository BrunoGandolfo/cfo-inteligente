import { useEffect, useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Layout from './components/layout/Layout';
import Home from './pages/Home';
import { Toaster } from 'react-hot-toast';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && (currentPage === 'home' || currentPage === 'login')) {
      setCurrentPage('dashboard');
    } else if (!token && currentPage === 'dashboard') {
      setCurrentPage('home');
    }
  }, [currentPage]);

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

  return (
    <>
      <Layout>
        <Dashboard />
      </Layout>
      <Toaster position="top-right" />
    </>
  );
}

export default App;
