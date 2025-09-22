import { useState, useEffect } from 'react';
import axios from 'axios';
import ModalIngreso from '../components/ModalIngreso';
import ModalGasto from '../components/ModalGasto';
import ModalRetiro from '../components/ModalRetiro';
import ModalDistribucion from '../components/ModalDistribucion';
import TablaOperacionesPro from '../components/TablaOperacionesPro';

function Dashboard() {
  const [resumenMensual, setResumenMensual] = useState(null);
  const [rentabilidad, setRentabilidad] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modalIngreso, setModalIngreso] = useState(false);
  const [modalGasto, setModalGasto] = useState(false);
  const [modalRetiro, setModalRetiro] = useState(false);
  const [modalDistribucion, setModalDistribucion] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  
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
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('Error cargando datos:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('es-UY', {
      style: 'currency',
      currency: 'UYU',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Cargando...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Sistema CFO Inteligente
          </h1>
          <p className="text-gray-600">Bienvenido, {userName}</p>
        </div>
      </div>

      {/* Contenedor principal con mejor organización */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        
        {/* Métricas en grid horizontal */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Ingresos */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Ingresos del mes</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatMoney(resumenMensual?.total_ingresos_uyu)}
                </p>
              </div>
              <div className="text-3xl">💰</div>
            </div>
          </div>

          {/* Gastos */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Gastos del mes</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatMoney(resumenMensual?.total_gastos_uyu)}
                </p>
              </div>
              <div className="text-3xl">💸</div>
            </div>
          </div>

          {/* Rentabilidad */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Rentabilidad</p>
                <p className="text-2xl font-bold text-blue-600">
                  {rentabilidad?.porcentaje?.toFixed(1) || 0}%
                </p>
              </div>
              <div className="text-3xl">📊</div>
            </div>
          </div>

          {/* Operaciones */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Operaciones</p>
                <p className="text-2xl font-bold">
                  {resumenMensual?.cantidad_operaciones || 0}
                </p>
              </div>
              <div className="text-3xl">📝</div>
            </div>
          </div>
        </div>

        {/* Botones de acción */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <h2 className="text-lg font-semibold mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <button
              onClick={() => setModalIngreso(true)}
              className="bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700"
            >
              + Registrar Ingreso
            </button>
            <button
              onClick={() => setModalGasto(true)}
              className="bg-red-600 text-white px-4 py-3 rounded-lg hover:bg-red-700"
            >
              - Registrar Gasto
            </button>
            <button
              onClick={() => setModalRetiro(true)}
              className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700"
            >
              ↓ Registrar Retiro
            </button>
            <button
              onClick={() => setModalDistribucion(true)}
              className="bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700"
            >
              ↔ Registrar Distribución
            </button>
          </div>
        </div>

        {/* Tabla de operaciones */}
        <TablaOperacionesPro refresh={refreshKey} />
      </div>

      {/* Modales con altura fija */}
      {modalIngreso && (
        <ModalIngreso
          isOpen={modalIngreso}
          onClose={() => setModalIngreso(false)}
          onSuccess={() => { cargarDatos(); setModalIngreso(false); }}
        />
      )}
      {modalGasto && (
        <ModalGasto
          isOpen={modalGasto}
          onClose={() => setModalGasto(false)}
          onSuccess={() => { cargarDatos(); setModalGasto(false); }}
        />
      )}
      {modalRetiro && (
        <ModalRetiro
          isOpen={modalRetiro}
          onClose={() => setModalRetiro(false)}
          onSuccess={() => { cargarDatos(); setModalRetiro(false); }}
        />
      )}
      {modalDistribucion && (
        <ModalDistribucion
          isOpen={modalDistribucion}
          onClose={() => setModalDistribucion(false)}
          onSuccess={() => { cargarDatos(); setModalDistribucion(false); }}
        />
      )}
    </div>
  );
}

export default Dashboard;
