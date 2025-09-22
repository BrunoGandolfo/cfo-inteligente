import { useState, useEffect } from 'react';
import axios from 'axios';
import ModalIngreso from '../components/ModalIngreso';
import ModalGasto from '../components/ModalGasto';
import ModalRetiro from '../components/ModalRetiro';
import ModalDistribucion from '../components/ModalDistribucion';

function Dashboard() {
  const [resumenMensual, setResumenMensual] = useState(null);
  const [rentabilidad, setRentabilidad] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modalIngreso, setModalIngreso] = useState(false);
  const [modalGasto, setModalGasto] = useState(false);
  const [modalRetiro, setModalRetiro] = useState(false);
  const [modalDistribucion, setModalDistribucion] = useState(false);
  const userName = localStorage.getItem('userName');

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      const [resumen, rent] = await Promise.all([
        axios.get('http://localhost:8000/api/reportes/resumen-mensual'),
        axios.get('http://localhost:8000/api/reportes/rentabilidad')
      ]);
      
      setResumenMensual(resumen.data);
      setRentabilidad(rent.data);
      setLoading(false);
    } catch (error) {
      console.error('Error cargando datos:', error);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  const handleOperacionSuccess = () => {
    cargarDatos();
    alert('Operación registrada exitosamente');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Cargando...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">CFO Inteligente - Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Hola, {userName}</span>
              <button
                onClick={handleLogout}
                className="text-sm bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Métricas */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Ingresos */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Ingresos del Mes</h3>
            <p className="mt-2 text-2xl font-semibold text-green-600">
              $ {resumenMensual?.ingresos?.uyu?.toLocaleString() || 0} UYU
            </p>
            <p className="text-sm text-gray-500">
              USD {resumenMensual?.ingresos?.usd?.toLocaleString() || 0}
            </p>
          </div>

          {/* Gastos */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Gastos del Mes</h3>
            <p className="mt-2 text-2xl font-semibold text-red-600">
              $ {resumenMensual?.gastos?.uyu?.toLocaleString() || 0} UYU
            </p>
            <p className="text-sm text-gray-500">
              USD {resumenMensual?.gastos?.usd?.toLocaleString() || 0}
            </p>
          </div>

          {/* Rentabilidad */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Rentabilidad</h3>
            <p className="mt-2 text-2xl font-semibold text-blue-600">
              {rentabilidad?.margen_operativo_porcentaje || 0}%
            </p>
            <p className="text-sm text-gray-500">Margen operativo</p>
          </div>

          {/* Operaciones */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500">Operaciones</h3>
            <p className="mt-2 text-2xl font-semibold text-gray-900">
              {resumenMensual?.cantidad_operaciones || 0}
            </p>
            <p className="text-sm text-gray-500">Este mes</p>
          </div>
        </div>

        {/* Acciones Rápidas */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button 
              onClick={() => setModalIngreso(true)}
              className="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700"
            >
              + Registrar Ingreso
            </button>
            <button 
              onClick={() => setModalGasto(true)}
              className="bg-red-600 text-white p-4 rounded-lg hover:bg-red-700"
            >
              - Registrar Gasto
            </button>
            <button 
              onClick={() => setModalRetiro(true)}
              className="bg-yellow-600 text-white p-4 rounded-lg hover:bg-yellow-700"
            >
              ↓ Registrar Retiro
            </button>
            <button 
              onClick={() => setModalDistribucion(true)}
              className="bg-purple-600 text-white p-4 rounded-lg hover:bg-purple-700"
            >
              ÷ Registrar Distribución
            </button>
          </div>
        </div>
      </main>

      {/* Modal de Ingreso */}
      <ModalIngreso
        isOpen={modalIngreso}
        onClose={() => setModalIngreso(false)}
        onSuccess={handleOperacionSuccess}
      />
      
      {/* Modal de Gasto */}
      <ModalGasto
        isOpen={modalGasto}
        onClose={() => setModalGasto(false)}
        onSuccess={handleOperacionSuccess}
      />
      
      {/* Modal de Retiro */}
      <ModalRetiro
        isOpen={modalRetiro}
        onClose={() => setModalRetiro(false)}
        onSuccess={handleOperacionSuccess}
      />
      
      {/* Modal de Distribución */}
      <ModalDistribucion
        isOpen={modalDistribucion}
        onClose={() => setModalDistribucion(false)}
        onSuccess={handleOperacionSuccess}
      />
    </div>
  );
}

export default Dashboard;
