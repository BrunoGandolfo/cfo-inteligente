/**
 * ColaboradorView.jsx
 * Vista limpia para colaboradores (no socios)
 * Sin métricas financieras, gráficos ni montos de dinero
 */

import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { Sun, Moon, LogOut, ArrowUpCircle, ArrowDownCircle, CheckCircle } from 'lucide-react';
import axiosClient from '../services/api/axiosClient';
import ModalIngreso from './ModalIngreso';
import ModalGasto from './ModalGasto';
import toast from 'react-hot-toast';

function ColaboradorView() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  const [operaciones, setOperaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showIngreso, setShowIngreso] = useState(false);
  const [showGasto, setShowGasto] = useState(false);
  
  const userName = localStorage.getItem('userName') || 'Colaborador';
  const fechaHoy = format(new Date(), "EEEE, d 'de' MMMM yyyy", { locale: es });

  // Toggle theme
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Fetch operaciones
  const fetchOperaciones = async () => {
    try {
      setLoading(true);
      const { data } = await axiosClient.get('/api/operaciones', { params: { limit: 10 } });
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

  const handleLogout = () => {
    toast.success('Sesión cerrada correctamente');
    setTimeout(() => {
      localStorage.clear();
      window.location.href = '/';
    }, 500);
  };

  const isDark = theme === 'dark';

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gray-900' : 'bg-gray-50'} transition-colors duration-300`}>
      {/* Header */}
      <header className={`${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b`}>
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <img 
              src="/logo-conexion.png" 
              alt="Conexión Consultora" 
              className="h-10 w-auto"
            />
          </div>

          {/* Right side */}
          <div className="flex items-center gap-4">
            {/* Theme toggle */}
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className={`p-2 rounded-lg ${isDark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'} transition-colors`}
              aria-label="Cambiar tema"
            >
              {isDark ? (
                <Sun className="w-5 h-5 text-yellow-400" />
              ) : (
                <Moon className="w-5 h-5 text-gray-600" />
              )}
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${
                isDark 
                  ? 'border-red-600 text-red-400 hover:bg-red-900/20' 
                  : 'border-red-500 text-red-600 hover:bg-red-50'
              } transition-colors font-medium text-sm`}
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Cerrar sesión</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Saludo */}
        <div className="mb-8">
          <h1 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Bienvenido, {userName}
          </h1>
          <p className={`text-sm mt-1 capitalize ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            {fechaHoy}
          </p>
        </div>

        {/* Tarjetas de acción */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          {/* Tarjeta Ingreso */}
          <button
            onClick={() => setShowIngreso(true)}
            className={`group p-8 rounded-xl border-2 transition-all duration-200 ${
              isDark 
                ? 'bg-gray-800 border-gray-700 hover:border-emerald-500 hover:bg-gray-800/80' 
                : 'bg-white border-gray-200 hover:border-emerald-500 hover:shadow-lg'
            }`}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`p-4 rounded-full mb-4 ${
                isDark ? 'bg-emerald-900/30' : 'bg-emerald-50'
              }`}>
                <ArrowUpCircle className="w-10 h-10 text-emerald-500" />
              </div>
              <h3 className={`text-xl font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Registrar Ingreso
              </h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Facturación, cobros y ventas
              </p>
            </div>
          </button>

          {/* Tarjeta Gasto */}
          <button
            onClick={() => setShowGasto(true)}
            className={`group p-8 rounded-xl border-2 transition-all duration-200 ${
              isDark 
                ? 'bg-gray-800 border-gray-700 hover:border-red-500 hover:bg-gray-800/80' 
                : 'bg-white border-gray-200 hover:border-red-500 hover:shadow-lg'
            }`}
          >
            <div className="flex flex-col items-center text-center">
              <div className={`p-4 rounded-full mb-4 ${
                isDark ? 'bg-red-900/30' : 'bg-red-50'
              }`}>
                <ArrowDownCircle className="w-10 h-10 text-red-500" />
              </div>
              <h3 className={`text-xl font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Registrar Gasto
              </h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Gastos operativos y servicios
              </p>
            </div>
          </button>
        </div>

        {/* Tabla de últimos registros */}
        <div className={`rounded-xl border ${
          isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <div className="p-4 border-b border-gray-700">
            <h2 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Mis últimos registros
            </h2>
          </div>
          
          <div className="overflow-x-auto">
            {loading ? (
              <div className={`p-8 text-center ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Cargando...
              </div>
            ) : operaciones.length === 0 ? (
              <div className={`p-8 text-center ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                No hay registros aún. ¡Registra tu primera operación!
              </div>
            ) : (
              <table className="w-full">
                <thead>
                  <tr className={isDark ? 'bg-gray-900/50' : 'bg-gray-50'}>
                    <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                      isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Fecha
                    </th>
                    <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                      isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Tipo
                    </th>
                    <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                      isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Descripción
                    </th>
                    <th className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                      isDark ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      Estado
                    </th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-gray-700' : 'divide-gray-200'}`}>
                  {operaciones.map((op) => (
                    <tr key={op.id} className={isDark ? 'hover:bg-gray-700/50' : 'hover:bg-gray-50'}>
                      <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                        {format(new Date(op.fecha), 'dd/MM/yyyy')}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          op.tipo_operacion === 'INGRESO'
                            ? isDark ? 'bg-emerald-900/30 text-emerald-400' : 'bg-emerald-100 text-emerald-700'
                            : isDark ? 'bg-red-900/30 text-red-400' : 'bg-red-100 text-red-700'
                        }`}>
                          {op.tipo_operacion === 'INGRESO' ? 'Ingreso' : 'Gasto'}
                        </span>
                      </td>
                      <td className={`px-4 py-3 text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                        {op.cliente || op.proveedor || op.descripcion || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 text-sm ${
                          isDark ? 'text-emerald-400' : 'text-emerald-600'
                        }`}>
                          <CheckCircle className="w-4 h-4" />
                          Registrado
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className={`mt-auto py-6 border-t ${
        isDark ? 'bg-gray-800/50 border-gray-700' : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            Este mes registraste <span className="font-semibold">{operacionesDelMes}</span> operaciones
          </p>
        </div>
      </footer>

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

