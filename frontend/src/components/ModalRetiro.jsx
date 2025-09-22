import { useState, useEffect } from 'react';
import axios from 'axios';

function ModalRetiro({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    monto_uyu: '',
    monto_usd: '',
    localidad: 'Montevideo',
    tipo_cambio: '',
    descripcion: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validar que al menos un monto esté presente
    if (!formData.monto_uyu && !formData.monto_usd) {
      setError('Debe ingresar al menos un monto (UYU o USD)');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      const dataToSend = {
        fecha: formData.fecha,
        monto_uyu: formData.monto_uyu ? parseFloat(formData.monto_uyu) : null,
        monto_usd: formData.monto_usd ? parseFloat(formData.monto_usd) : null,
        localidad: formData.localidad,
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        descripcion: formData.descripcion || null
      };

      await axios.post('http://localhost:8000/api/operaciones/retiro', dataToSend);
      
      onSuccess();
      onClose();
      
      // Reset form
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        monto_uyu: '',
        monto_usd: '',
        localidad: 'Montevideo',
        tipo_cambio: '',
        descripcion: ''
      });
    } catch (error) {
      console.error('Error completo:', error);
      setError(error.response?.data?.detail || 'Error al registrar el retiro');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 p-2">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[70vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-4 pb-2 border-b">
          <h2 className="text-lg font-bold text-yellow-600">Registrar Retiro</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">
            ✕
          </button>
        </div>

        {/* Contenido más simple */}
        <div className="p-4">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-2 py-1 rounded mb-2 text-xs">
              {error}
            </div>
          )}

          <form id="formRetiro" onSubmit={handleSubmit}>
            {/* Fecha y Localidad */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div>
                <label className="block text-xs font-medium text-gray-700">Fecha</label>
                <input
                  type="date"
                  required
                  value={formData.fecha}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setFormData({...formData, fecha: e.target.value})}
                  className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Localidad</label>
                <select
                  value={formData.localidad}
                  onChange={(e) => setFormData({...formData, localidad: e.target.value})}
                  className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                >
                  <option value="Montevideo">Montevideo</option>
                  <option value="Mercedes">Mercedes</option>
                </select>
              </div>
            </div>

            {/* Tipo de cambio */}
            <div className="mb-3">
              <label className="block text-xs font-medium text-gray-700">Tipo de Cambio (USD → UYU)</label>
              <input
                type="number"
                required
                step="0.01"
                min="0.01"
                value={formData.tipo_cambio}
                onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
              />
            </div>

            {/* Montos separados */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div>
                <label className="block text-xs font-medium text-gray-700">Retiro en UYU</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.monto_uyu}
                  onChange={(e) => setFormData({...formData, monto_uyu: e.target.value})}
                  className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                  placeholder="$ 0.00"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700">Retiro en USD</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.monto_usd}
                  onChange={(e) => setFormData({...formData, monto_usd: e.target.value})}
                  className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                  placeholder="USD 0.00"
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 mb-3">* Ingrese al menos un monto</p>

            {/* Descripción */}
            <div className="mb-3">
              <label className="block text-xs font-medium text-gray-700">Descripción</label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm"
                rows="2"
                placeholder="Opcional"
              />
            </div>
          </form>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-4 pt-2 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancelar
          </button>
          <button
            type="submit"
            form="formRetiro"
            disabled={loading}
            className="px-4 py-2 text-sm text-white bg-yellow-600 rounded hover:bg-yellow-700 disabled:opacity-50"
          >
            {loading ? 'Guardando...' : 'Guardar Retiro'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ModalRetiro;
