import { useState, useEffect } from 'react';
import axios from 'axios';

function TablaOperacionesPro({ refresh }) {
  const [operaciones, setOperaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOp, setSelectedOp] = useState(null);

  // Configuración de colores por tipo (consenso de todos los expertos)
  const tipoConfig = {
    INGRESO: 'bg-green-100 text-green-800 border-green-200',
    GASTO: 'bg-red-100 text-red-800 border-red-200',
    RETIRO: 'bg-amber-100 text-amber-800 border-amber-200',
    DISTRIBUCION: 'bg-blue-100 text-blue-800 border-blue-200'
  };

  // Formateo compacto de fecha (DD/MM)
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${day}/${month}`;
  };

  // Formateo de moneda SIN conversión (punto clave de todos los expertos)
  const formatMoney = (amount, monedaOriginal) => {
    if (!amount && amount !== 0) return '0';
    
    // Detectar moneda basándonos en los montos
    let moneda = 'UYU';
    if (monedaOriginal === 'USD' || (amount < 10000 && amount > 100)) {
      moneda = 'USD';
    }
    
    const symbol = moneda === 'USD' ? 'USD' : '$';
    const decimals = moneda === 'USD' ? 2 : 0;
    
    return `${symbol} ${parseFloat(amount).toLocaleString('es-UY', { 
      minimumFractionDigits: decimals, 
      maximumFractionDigits: decimals 
    })}`;
  };

  // Detectar moneda original de la operación
  const detectarMoneda = (op) => {
    // Si el monto USD es significativo y la relación es correcta, fue en USD
    if (op.monto_usd > 100 && op.monto_uyu / op.monto_usd > 30) {
      return { moneda: 'USD', monto: op.monto_usd };
    }
    return { moneda: 'UYU', monto: op.monto_uyu };
  };

  const fetchOperaciones = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/api/operaciones', {
        params: { limit: 20 }
      });
      setOperaciones(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const anularOperacion = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('¿Anular esta operación?')) return;
    
    try {
      await axios.patch(`http://localhost:8000/api/operaciones/${id}/anular`);
      fetchOperaciones();
      if (refresh) refresh();
    } catch (error) {
      alert('Error al anular');
    }
  };

  useEffect(() => {
    fetchOperaciones();
  }, [refresh]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500">Cargando operaciones...</div>
      </div>
    );
  }

  return (
    <>
      {/* Tabla principal - Solo 5 columnas como sugieren TODOS los expertos */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-3 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Operaciones</h3>
        </div>
        
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Fecha
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Tipo
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Tercero
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Monto
              </th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {operaciones.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                  No hay operaciones registradas
                </td>
              </tr>
            ) : (
              operaciones.map((op) => {
                const tipoUpper = (op.tipo || op.tipo_operacion || '').toUpperCase();
                const { moneda, monto } = detectarMoneda(op);
                
                return (
                  <tr 
                    key={op.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedOp(op)}
                  >
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDate(op.fecha)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${tipoConfig[tipoUpper] || 'bg-gray-100'}`}>
                        {tipoUpper}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {op.cliente || op.proveedor || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-bold">
                      {formatMoney(monto, moneda)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={(e) => {e.stopPropagation(); setSelectedOp(op);}}
                        className="text-blue-600 hover:text-blue-800 text-sm mr-3"
                      >
                        Ver
                      </button>
                      <button
                        onClick={(e) => anularOperacion(op.id, e)}
                        className="text-red-600 hover:text-red-800 text-sm"
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

      {/* Modal de detalles - Información completa como sugieren los expertos */}
      {selectedOp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              {/* Header del modal */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-xl font-semibold">Detalle de Operación</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    ID: {selectedOp.id.substring(0, 8)}...
                  </p>
                </div>
                <button
                  onClick={() => setSelectedOp(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Información principal */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="text-sm text-gray-500">Fecha completa</label>
                  <p className="font-medium">{new Date(selectedOp.fecha).toLocaleString('es-UY')}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Tipo de operación</label>
                  <p className="font-medium">{(selectedOp.tipo || selectedOp.tipo_operacion || '').toUpperCase()}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Cliente</label>
                  <p className="font-medium">{selectedOp.cliente || '-'}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Proveedor</label>
                  <p className="font-medium">{selectedOp.proveedor || '-'}</p>
                </div>
              </div>

              {/* Información financiera detallada */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h5 className="font-semibold mb-3">Información Financiera</h5>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">Monto en UYU</label>
                    <p className="font-medium text-lg">$ {formatMoney(selectedOp.monto_uyu, 'UYU')}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Monto en USD</label>
                    <p className="font-medium text-lg">USD {formatMoney(selectedOp.monto_usd, 'USD')}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Tipo de cambio aplicado</label>
                    <p className="font-medium">
                      {selectedOp.monto_usd > 0 ? 
                        (selectedOp.monto_uyu / selectedOp.monto_usd).toFixed(2) : 
                        'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">Fecha del TC</label>
                    <p className="font-medium">{formatDate(selectedOp.fecha)}</p>
                  </div>
                </div>
              </div>

              {/* Descripción si existe */}
              {selectedOp.descripcion && (
                <div className="mb-6">
                  <label className="text-sm text-gray-500">Descripción</label>
                  <p className="mt-1 p-3 bg-gray-50 rounded">{selectedOp.descripcion}</p>
                </div>
              )}

              {/* Acciones */}
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setSelectedOp(null)}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
                >
                  Cerrar
                </button>
                <button
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                >
                  Editar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default TablaOperacionesPro;
