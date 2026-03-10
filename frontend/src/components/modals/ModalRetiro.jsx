import { useState, useEffect } from 'react';
import axiosClient from '../../services/api/axiosClient';
import toast from 'react-hot-toast';
import ModalBase from '../shared/ModalBase';

function ModalRetiro({ isOpen, onClose, onSuccess, setLoading, editMode }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    localidad: 'Montevideo',
    monto_uyu: '',
    monto_usd: '',
    tipo_cambio: '',
    descripcion: ''
  });
  
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (editMode) {
        setFormData({
          fecha: editMode.fecha,
          localidad: editMode.localidad || 'Montevideo',
          monto_uyu: editMode.monto_uyu?.toString() || '',
          monto_usd: editMode.monto_usd?.toString() || '',
          tipo_cambio: editMode.tipo_cambio?.toString() || '',
          descripcion: editMode.descripcion || ''
        });
      } else {
        cargarTipoCambio();
      }
    }
  }, [isOpen, editMode]);

  const cargarTipoCambio = async () => {
    try {
      const response = await axiosClient.get('/api/tipo-cambio/venta');
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
        localidad: formData.localidad,
        monto_uyu: parseFloat(formData.monto_uyu) || 0,
        monto_usd: parseFloat(formData.monto_usd) || 0,
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        descripcion: formData.descripcion || null
      };

      if (editMode) {
        await axiosClient.patch(`/api/operaciones/${editMode.id}`, dataToSend);
        toast.success('✅ Retiro actualizado correctamente');
      } else {
        await axiosClient.post('/api/operaciones/retiro', dataToSend);
        toast.success('✅ Retiro registrado correctamente');
      }
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        localidad: 'Montevideo',
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
      title={editMode ? "Editar Retiro" : "Registrar Retiro"}
      submitLabel={editMode ? "Actualizar" : "Guardar"}
      onSubmit={handleSubmitInterno}
      isLoading={localLoading}
      size="max-w-2xl"
      borderColor="border-retiro"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
        <div>
          <label className="block text-xs font-medium text-text-secondary">Fecha</label>
          <input
            type="date"
            required
            value={formData.fecha}
            max={new Date().toISOString().split('T')[0]}
            onChange={(e) => setFormData({...formData, fecha: e.target.value})}
            className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary">Localidad</label>
          <select
            value={formData.localidad}
            onChange={(e) => setFormData({...formData, localidad: e.target.value})}
            className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          >
            <option value="Montevideo">Montevideo</option>
            <option value="Mercedes">Mercedes</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-2">
        <div>
          <label className="block text-xs font-medium text-text-secondary">Monto UYU</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.monto_uyu}
            onChange={(e) => setFormData({...formData, monto_uyu: e.target.value})}
            className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary">Monto USD</label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={formData.monto_usd}
            onChange={(e) => setFormData({...formData, monto_usd: e.target.value})}
            className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-text-secondary">T.C.</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={formData.tipo_cambio}
            onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
            className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>
      </div>

      <div className="mb-2">
        <label className="block text-xs font-medium text-text-secondary">Descripción</label>
        <textarea
          value={formData.descripcion}
          onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
          className="w-full px-1 py-1 border border-border rounded text-xs bg-surface text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          rows="1"
          placeholder="Opcional"
        />
      </div>
    </ModalBase>
  );
}

export default ModalRetiro;
