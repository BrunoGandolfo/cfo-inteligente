import { useState, useEffect } from 'react';
import axios from 'axios';

function TablaOperaciones({ refresh }) {
  const [operaciones, setOperaciones] = useState([]);
  const [loading, setLoading] = useState(true);

  // Colores por tipo de operación
  const getColorByTipo = (tipo) => {
    const tipoUpper = (tipo || '').toUpperCase();
    switch(tipoUpper) {
      case 'INGRESO': return 'text-green-600 bg-green-50';
      case 'GASTO': return 'text-red-600 bg-red-50';
      case 'RETIRO': return 'text-blue-600 bg-blue-50';
      case 'DISTRIBUCION': return 'text-purple-600 bg-purple-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // Formatear moneda
  const formatMoney = (amount, currency = 'UYU') => {
    if (!amount && amount !== 0) return '-';
    const symbol = currency === 'USD' ? 'U$S' : '$';
    return `${symbol} ${parseFloat(amount).toLocaleString('es-UY', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    })}`;
  };

  // Formatear fecha
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-UY');
  };

  // Cargar operaciones
  const fetchOperaciones = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/operaciones', {
        params: { limit: 20 }
      });
      console.log('Operaciones recibidas:', response.data);
      setOperaciones(response.data);
    } catch (error) {
      console.error('Error cargando operaciones:', error);
    } finally {
      setLoading(false);
    }
  };

  // Anular operación (soft delete)
  const anularOperacion = async (id) => {
    if (!window.confirm('¿Está seguro de anular esta operación?')) {
      return;
    }
    
    try {
      await axios.patch(`http://localhost:8000/api/operaciones/${id}/anular`);
      fetchOperaciones(); // Recargar
      if (refresh) refresh(); // Actualizar dashboard
    } catch (error) {
      alert('Error al anular operación');
    }
  };

  useEffect(() => {
    fetchOperaciones();
  }, [refresh]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-10 bg-gray-100 rounded mb-2"></div>
          <div className="h-10 bg-gray-100 rounded mb-2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Últimas Operaciones
        </h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cliente/Prov
              </th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monto UYU
              </th>
              <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monto USD
              </th>
              <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Descripción
              </th>
              <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {operaciones.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                  No hay operaciones registradas
                </td>
              </tr>
            ) : (
              operaciones.map((op) => {
                const tipoUpper = (op.tipo || '').toUpperCase();
                return (
                  <tr key={op.id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(op.fecha)}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getColorByTipo(op.tipo)}`}>
                        {tipoUpper}
                      </span>
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-900">
                      {op.cliente || op.proveedor || '-'}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatMoney(op.monto_uyu, 'UYU')}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                      {formatMoney(op.monto_usd, 'USD')}
                    </td>
                    <td className="px-3 py-2 text-sm text-gray-900">
                      {op.descripcion || '-'}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-center">
                      <button
                        onClick={() => anularOperacion(op.id)}
                        className="text-red-600 hover:text-red-900 text-sm font-medium"
                      >
                        Anular
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TablaOperaciones;
