import { useState, useEffect } from 'react';
import axios from 'axios';
import ModalBase from './shared/ModalBase';

function ModalRetiro({ isOpen, onClose, onSuccess, setLoading }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    socio_id: '',
    monto_uyu: '',
    monto_usd: '',
    tipo_cambio: '',
    descripcion: ''
  });
  
  const [socios] = useState([
    { id: '1e8aa519-c5e9-4c49-9e3e-f5c8d91d3a2e', nombre: 'Agustina' },
    { id: '2f9bb62a-d6fa-5d5a-af4f-06d9e82e4b3f', nombre: 'Viviana' },
    { id: '3g0cc73b-e701-6e6b-bg50-17eaf93f5c40', nombre: 'Gonzalo' },
    { id: '4h1dd84c-f812-7f7c-ch61-28fbg040gd51', nombre: 'Pancho' },
    { id: '5i2ee95d-0923-8g8d-di72-39gch151he62', nombre: 'Bruno' }
  ]);
  
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      cargarTipoCambio();
    }
  }, [isOpen]);

  const cargarTipoCambio = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tipo-cambio/venta');
      setFormData(prev => ({ ...prev, tipo_cambio: response.data.valor.toString() }));
    } catch {
      setFormData(prev => ({ ...prev, tipo_cambio: '40.50' }));
    }
  };

  const handleSubmitInterno = async () => {
    setLocalLoading(true);
    if (setLoading) setLoading(true);

    try {
      const dataToSend = {
        fecha: formData.fecha,
        socio_id: formData.socio_id,
        monto_uyu: parseFloat(formData.monto_uyu) || 0,
        monto_usd: parseFloat(formData.monto_usd) || 0,
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        descripcion: formData.descripcion || null
      };

      await axios.post('http://localhost:8000/api/operaciones/retiro', dataToSend);
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        socio_id: '',
        monto_uyu: '',
        monto_usd: '',
        tipo_cambio: '',
        descripcion: ''
      });
    } finally {
      setLocalLoading(false);
      if (setLoading) setLoading(false);
    }
  };

  return (
    <ModalBase
      isOpen={isOpen}
      onClose={onClose}
      title="Registrar Retiro"
      onSubmit={handleSubmitInterno}
      isLoading={localLoading}
      size="max-w-md"
    >
      <div className="grid grid-cols-2 gap-2 mb-2">
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
          <label className="block text-xs font-medium text-gray-700">Socio *</label>
          <select
            required
            value={formData.socio_id}
            onChange={(e) => setFormData({...formData, socio_id: e.target.value})}
            className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
          >
            <option value="">Seleccione...</option>
            {socios.map(socio => (
              <option key={socio.id} value={socio.id}>{socio.nombre}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-2">
        <div>
          <label className="block text-xs font-medium text-gray-700">Monto UYU</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.monto_uyu}
            onChange={(e) => setFormData({...formData, monto_uyu: e.target.value})}
            className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700">Monto USD</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.monto_usd}
            onChange={(e) => setFormData({...formData, monto_usd: e.target.value})}
            className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700">T.C.</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={formData.tipo_cambio}
            onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
            className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
          />
        </div>
      </div>

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
    </ModalBase>
  );
}

export default ModalRetiro;

