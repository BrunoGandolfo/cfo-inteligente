import { useState, useEffect } from 'react';
import axios from 'axios';

function ModalDistribucion({ isOpen, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    tipo_cambio: '',
    localidad: 'Montevideo',
    descripcion: '',
    agustina_uyu: '', agustina_usd: '',
    viviana_uyu: '', viviana_usd: '',
    gonzalo_uyu: '', gonzalo_usd: '',
    pancho_uyu: '', pancho_usd: '',
    bruno_uyu: '', bruno_usd: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const socios = ['Agustina', 'Viviana', 'Gonzalo', 'Pancho', 'Bruno'];

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
      setFormData(prev => ({ ...prev, tipo_cambio: '40.50' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const hayAlgunMonto = socios.some(socio => {
      const nombreLower = socio.toLowerCase();
      return formData[`${nombreLower}_uyu`] || formData[`${nombreLower}_usd`];
    });

    if (!hayAlgunMonto) {
      setError('Debe ingresar al menos un monto');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      const dataToSend = {
        fecha: formData.fecha,
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        localidad: formData.localidad,
        descripcion: formData.descripcion || null,
        agustina_uyu: formData.agustina_uyu ? parseFloat(formData.agustina_uyu) : null,
        agustina_usd: formData.agustina_usd ? parseFloat(formData.agustina_usd) : null,
        viviana_uyu: formData.viviana_uyu ? parseFloat(formData.viviana_uyu) : null,
        viviana_usd: formData.viviana_usd ? parseFloat(formData.viviana_usd) : null,
        gonzalo_uyu: formData.gonzalo_uyu ? parseFloat(formData.gonzalo_uyu) : null,
        gonzalo_usd: formData.gonzalo_usd ? parseFloat(formData.gonzalo_usd) : null,
        pancho_uyu: formData.pancho_uyu ? parseFloat(formData.pancho_uyu) : null,
        pancho_usd: formData.pancho_usd ? parseFloat(formData.pancho_usd) : null,
        bruno_uyu: formData.bruno_uyu ? parseFloat(formData.bruno_uyu) : null,
        bruno_usd: formData.bruno_usd ? parseFloat(formData.bruno_usd) : null
      };

      await axios.post('http://localhost:8000/api/operaciones/distribucion', dataToSend);
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        tipo_cambio: '',
        localidad: 'Montevideo',
        descripcion: '',
        agustina_uyu: '', agustina_usd: '',
        viviana_uyu: '', viviana_usd: '',
        gonzalo_uyu: '', gonzalo_usd: '',
        pancho_uyu: '', pancho_usd: '',
        bruno_uyu: '', bruno_usd: ''
      });
    } catch (error) {
      setError(error.response?.data?.detail || 'Error al registrar');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50 p-2">
      <div className="bg-white rounded-lg w-full max-w-md max-h-[70vh] flex flex-col">
        {/* Header compacto */}
        <div className="flex justify-between items-center p-3 pb-2 border-b">
          <h2 className="text-md font-bold text-purple-600">Distribución</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {/* Contenido scrolleable */}
        <div className="flex-1 overflow-y-auto p-3">
          {error && (
            <div className="bg-red-100 text-red-700 px-2 py-1 rounded mb-2 text-xs">{error}</div>
          )}

          <form id="formDistribucion" onSubmit={handleSubmit}>
            {/* Primera línea: Fecha, TC, Localidad */}
            <div className="grid grid-cols-3 gap-1 mb-2">
              <div>
                <label className="text-xs text-gray-700">Fecha</label>
                <input
                  type="date"
                  required
                  value={formData.fecha}
                  max={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setFormData({...formData, fecha: e.target.value})}
                  className="w-full px-1 py-0.5 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs text-gray-700">T.C.</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  value={formData.tipo_cambio}
                  onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
                  className="w-full px-1 py-0.5 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs text-gray-700">Local</label>
                <select
                  value={formData.localidad}
                  onChange={(e) => setFormData({...formData, localidad: e.target.value})}
                  className="w-full px-1 py-0.5 border rounded text-xs"
                >
                  <option value="Montevideo">MVD</option>
                  <option value="Mercedes">Merc</option>
                </select>
              </div>
            </div>

            {/* Tabla compacta de socios */}
            <div className="border rounded p-1 mb-2">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-1">Socio</th>
                    <th className="text-center">UYU</th>
                    <th className="text-center">USD</th>
                  </tr>
                </thead>
                <tbody>
                  {socios.map((socio) => {
                    const nombreLower = socio.toLowerCase();
                    return (
                      <tr key={socio}>
                        <td className="py-1">{socio}</td>
                        <td className="px-1">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={formData[`${nombreLower}_uyu`]}
                            onChange={(e) => setFormData({...formData, [`${nombreLower}_uyu`]: e.target.value})}
                            className="w-full px-1 border rounded text-xs"
                            placeholder="0"
                          />
                        </td>
                        <td className="px-1">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={formData[`${nombreLower}_usd`]}
                            onChange={(e) => setFormData({...formData, [`${nombreLower}_usd`]: e.target.value})}
                            className="w-full px-1 border rounded text-xs"
                            placeholder="0"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Descripción mini */}
            <textarea
              value={formData.descripcion}
              onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
              className="w-full px-1 py-0.5 border rounded text-xs"
              rows="1"
              placeholder="Descripción (opcional)"
            />
          </form>
        </div>

        {/* Footer fijo con botones */}
        <div className="flex justify-end gap-2 p-3 pt-2 border-t">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 text-xs text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancelar
          </button>
          <button
            type="submit"
            form="formDistribucion"
            disabled={loading}
            className="px-3 py-1 text-xs text-white bg-purple-600 rounded hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ModalDistribucion;
