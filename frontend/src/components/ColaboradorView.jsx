/**
 * ColaboradorView.jsx
 * Vista limpia para colaboradores (no socios)
 * Sin métricas financieras, gráficos ni montos de dinero
 * El Header y Sidebar vienen del Layout principal
 */

import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { ArrowUpCircle, ArrowDownCircle, CalendarCheck } from 'lucide-react';
import axiosClient from '../services/api/axiosClient';
import ModalIngreso from './ModalIngreso';
import ModalGasto from './ModalGasto';

function ColaboradorView() {
  const [operaciones, setOperaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showIngreso, setShowIngreso] = useState(false);
  const [showGasto, setShowGasto] = useState(false);
  const [fraseMotivacional, setFraseMotivacional] = useState('');
  
  const userName = localStorage.getItem('userName') || 'Colaborador';
  const fechaHoy = format(new Date(), "EEEE, d 'de' MMMM yyyy", { locale: es });

  // Fetch frase motivacional personalizada
  useEffect(() => {
    const fetchFrase = async () => {
      try {
        const { data } = await axiosClient.get('/api/frases/motivacional');
        setFraseMotivacional(data.frase);
      } catch (error) {
        setFraseMotivacional('¡A seguir registrando con excelencia!');
      }
    };
    fetchFrase();
  }, []);

  // Fetch operaciones
  const fetchOperaciones = async () => {
    try {
      setLoading(true);
      const { data } = await axiosClient.get('/api/operaciones', { params: { limit: 100 } });
      // Filtrar solo ingresos y gastos (no retiros ni distribuciones)
      const filtradas = (data || []).filter(op => 
        op.tipo_operacion === 'INGRESO' || op.tipo_operacion === 'GASTO'
      );
      setOperaciones(filtradas);
    } catch (error) {
      console.error('Error fetching operaciones:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOperaciones();
  }, []);

  // Contar operaciones del mes actual
  const operacionesDelMes = operaciones.filter(op => {
    const fechaOp = new Date(op.fecha);
    const hoy = new Date();
    return fechaOp.getMonth() === hoy.getMonth() && fechaOp.getFullYear() === hoy.getFullYear();
  }).length;

  return (
    <div className="min-h-[calc(100vh-5rem)] flex flex-col items-center justify-start py-8 px-4">
      {/* Saludo - centrado */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Bienvenido, {userName}
        </h1>
        <p className="text-sm mt-1 capitalize text-gray-500 dark:text-gray-400">
          {fechaHoy}
        </p>
      </div>

      {/* Tarjetas de acción - centradas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10 w-full max-w-2xl">
        {/* Tarjeta Ingreso */}
        <button
          onClick={() => setShowIngreso(true)}
          className="group p-8 rounded-xl border-2 transition-all duration-200 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-emerald-500 hover:shadow-lg dark:hover:bg-gray-800/80"
        >
          <div className="flex flex-col items-center text-center">
            <div className="p-4 rounded-full mb-4 bg-emerald-50 dark:bg-emerald-900/30">
              <ArrowUpCircle className="w-10 h-10 text-emerald-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
              Registrar Ingreso
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Facturación, cobros y ventas
            </p>
          </div>
        </button>

        {/* Tarjeta Gasto */}
        <button
          onClick={() => setShowGasto(true)}
          className="group p-8 rounded-xl border-2 transition-all duration-200 bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-red-500 hover:shadow-lg dark:hover:bg-gray-800/80"
        >
          <div className="flex flex-col items-center text-center">
            <div className="p-4 rounded-full mb-4 bg-red-50 dark:bg-red-900/30">
              <ArrowDownCircle className="w-10 h-10 text-red-500" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">
              Registrar Gasto
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Gastos operativos y servicios
            </p>
          </div>
        </button>
      </div>

      {/* Card de resumen mensual - minimalista */}
      <div className="w-full max-w-2xl">
        <div className="rounded-xl border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm p-8">
          <div className="flex flex-col items-center text-center">
            <div className="p-3 rounded-full mb-4 bg-blue-50 dark:bg-blue-900/20">
              <CalendarCheck className="w-8 h-8 text-blue-500 dark:text-blue-400" />
            </div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Operaciones este mes
            </p>
            {loading ? (
              <div className="text-4xl font-bold text-gray-300 dark:text-gray-600">--</div>
            ) : (
              <div className="text-4xl font-bold text-gray-900 dark:text-white">
                {operacionesDelMes}
              </div>
            )}
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
              {fraseMotivacional || 'Cargando...'}
            </p>
          </div>
        </div>
      </div>

      {/* Modales */}
      {showIngreso && (
        <ModalIngreso
          isOpen={showIngreso}
          onClose={() => setShowIngreso(false)}
          onSuccess={() => {
            setShowIngreso(false);
            fetchOperaciones();
          }}
        />
      )}
      {showGasto && (
        <ModalGasto
          isOpen={showGasto}
          onClose={() => setShowGasto(false)}
          onSuccess={() => {
            setShowGasto(false);
            fetchOperaciones();
          }}
        />
      )}
    </div>
  );
}

export default ColaboradorView;
