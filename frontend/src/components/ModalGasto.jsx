import { useState, useEffect } from 'react';
import axios from 'axios';

function ModalGasto({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    proveedor: '',
    proveedor_telefono: '',
    area_id: '',
    localidad: 'Montevideo',
    monto_original: '',
    moneda_original: 'UYU',
    tipo_cambio: '',
    descripcion: ''
  });
  
  const [areas] = useState([
    { id: 'd3aff49c-748c-4d1d-bc47-cdda1cfb913d', nombre: 'Jurídica' },
    { id: '53ba7821-8836-4e74-ad56-a288d290881d', nombre: 'Notarial' },
    { id: '14700c01-3b3d-49c6-8e2e-f3ebded1b1bb', nombre: 'Contable' },
    { id: '11c64c64-c7f6-4e85-9c26-b577c3d7a5b7', nombre: 'Recuperación' },
    { id: 'b11006d3-6cfc-4766-9201-ab56274401a6', nombre: 'Gastos Generales' },
    { id: '651dfb5c-15d8-41e2-8339-785b137f44f2', nombre: 'Otros' }
  ]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [proveedorSuggestions, setProveedorSuggestions] = useState([]);

  useEffect(() => {
    if (isOpen) {
      cargarTipoCambio();
    }
  }, [isOpen]);

  const cargarTipoCambio = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tipo-cambio/venta');
      setFormData(prev => ({ ...prev, tipo_cambio: response.data.valor.toString() }));
    } catch (error) {
      console.error('Error cargando tipo de cambio:', error);
      setFormData(prev => ({ ...prev, tipo_cambio: '40.50' }));
    }
  };

  const buscarProveedores = async (query) => {
    if (query.length < 2) {
      setProveedorSuggestions([]);
      return;
    }
    
    try {
      const response = await axios.get(`http://localhost:8000/api/operaciones/proveedores/buscar?q=${query}`);
      setProveedorSuggestions(response.data);
    } catch (error) {
      console.error('Error buscando proveedores:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const tipoCambioParaEnviar = formData.moneda_original === 'UYU' 
        ? 1 
        : parseFloat(formData.tipo_cambio) || 40.50;

      const dataToSend = {
        fecha: formData.fecha,
        proveedor: formData.proveedor || null,
        proveedor_telefono: formData.proveedor_telefono || null,
        area_id: formData.area_id,
        localidad: formData.localidad,
        monto_original: parseFloat(formData.monto_original),
        moneda_original: formData.moneda_original,
        tipo_cambio: tipoCambioParaEnviar,
        descripcion: formData.descripcion || null
      };

      await axios.post('http://localhost:8000/api/operaciones/gasto', dataToSend);
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        proveedor: '',
        proveedor_telefono: '',
        area_id: '',
        localidad: 'Montevideo',
        monto_original: '',
        moneda_original: 'UYU',
        tipo_cambio: '',
        descripcion: ''
      });
      setProveedorSuggestions([]);
    } catch (error) {
      console.error('Error completo:', error);
      setError(error.response?.data?.detail || 'Error al registrar el gasto');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 p-2">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 pb-2 border-b">
          <h2 className="text-lg font-bold text-red-600">Registrar Gasto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">
            ✕
          </button>
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-y-auto p-4">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-2 py-1 rounded mb-2 text-xs">
              {error}
            </div>
          )}

          <form id="formGasto" onSubmit={handleSubmit}>
            {/* Primera fila: Fecha, Área, Localidad */}
            <div className="grid grid-cols-3 gap-2 mb-2">
              <div>
                <label className="block text-xs font-medium text-gray-700">Fecha</label>
                <input
                  type="date"
                  required
                  value={formData.fecha}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setFormData({...formData, fecha: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Área *</label>
                <select
                  required
                  value={formData.area_id}
                  onChange={(e) => setFormData({...formData, area_id: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="">Seleccione...</option>
                  {areas.map(area => (
                    <option key={area.id} value={area.id}>{area.nombre}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Local</label>
                <select
                  value={formData.localidad}
                  onChange={(e) => setFormData({...formData, localidad: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="Montevideo">MVD</option>
                  <option value="Mercedes">Mercedes</option>
                </select>
              </div>
            </div>

            {/* Segunda fila: Proveedor con autocomplete */}
            <div className="mb-2 relative">
              <label className="block text-xs font-medium text-gray-700">Proveedor</label>
              <input
                type="text"
                value={formData.proveedor}
                onChange={(e) => {
                  setFormData({...formData, proveedor: e.target.value});
                  buscarProveedores(e.target.value);
                }}
                className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                placeholder="Escriba para buscar..."
              />
              {proveedorSuggestions.length > 0 && (
                <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-b-md shadow-lg max-h-32 overflow-y-auto">
                  {proveedorSuggestions.map((prov) => (
                    <div
                      key={prov.id}
                      onClick={() => {
                        setFormData({...formData, proveedor: prov.nombre});
                        setProveedorSuggestions([]);
                      }}
                      className="px-2 py-1 hover:bg-gray-100 cursor-pointer text-xs"
                    >
                      {prov.nombre}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Tercera fila: Moneda, Monto, Tipo Cambio */}
            <div className="grid grid-cols-3 gap-2 mb-2">
              <div>
                <label className="block text-xs font-medium text-gray-700">Moneda</label>
                <select
                  value={formData.moneda_original}
                  onChange={(e) => setFormData({...formData, moneda_original: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                >
                  <option value="UYU">UYU</option>
                  <option value="USD">USD</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Monto *</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0.01"
                  value={formData.monto_original}
                  onChange={(e) => setFormData({...formData, monto_original: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">T.C.</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0.01"
                  value={formData.tipo_cambio}
                  onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
                  className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                />
              </div>
            </div>

            {/* Descripción */}
            <div className="mb-2">
              <label className="block text-xs font-medium text-gray-700">Descripción</label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
                rows="1"
                placeholder="Opcional"
              />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-3 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancelar
          </button>
          <button
            type="submit"
            form="formGasto"
            disabled={loading}
            className="px-3 py-1.5 text-xs text-white bg-red-600 rounded hover:bg-red-700 disabled:opacity-50"
          >
            {loading ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ModalGasto;
