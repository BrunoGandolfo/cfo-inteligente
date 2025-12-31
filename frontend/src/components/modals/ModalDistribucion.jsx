import { useState, useEffect } from 'react';
import axiosClient from '../../services/api/axiosClient';
import toast from 'react-hot-toast';
import ModalBase from '../shared/ModalBase';

function ModalDistribucion({ isOpen, onClose, onSuccess, setLoading, editMode }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    localidad: 'Montevideo',
    tipo_cambio: '',
    descripcion: '',
    // 5 socios con UYU y USD cada uno
    agustina_uyu: '',
    agustina_usd: '',
    viviana_uyu: '',
    viviana_usd: '',
    gonzalo_uyu: '',
    gonzalo_usd: '',
    pancho_uyu: '',
    pancho_usd: '',
    bruno_uyu: '',
    bruno_usd: ''
  });
  
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (editMode) {
        // Modo edición: precargar datos
        setFormData({
          fecha: editMode.fecha,
          localidad: editMode.localidad || 'Montevideo',
          tipo_cambio: editMode.tipo_cambio?.toString() || '',
          descripcion: editMode.descripcion || '',
          // Los montos de socios se cargarán dinámicamente
          agustina_uyu: '',
          agustina_usd: '',
          viviana_uyu: '',
          viviana_usd: '',
          gonzalo_uyu: '',
          gonzalo_usd: '',
          pancho_uyu: '',
          pancho_usd: '',
          bruno_uyu: '',
          bruno_usd: ''
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
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        agustina_uyu: parseFloat(formData.agustina_uyu) || null,
        agustina_usd: parseFloat(formData.agustina_usd) || null,
        viviana_uyu: parseFloat(formData.viviana_uyu) || null,
        viviana_usd: parseFloat(formData.viviana_usd) || null,
        gonzalo_uyu: parseFloat(formData.gonzalo_uyu) || null,
        gonzalo_usd: parseFloat(formData.gonzalo_usd) || null,
        pancho_uyu: parseFloat(formData.pancho_uyu) || null,
        pancho_usd: parseFloat(formData.pancho_usd) || null,
        bruno_uyu: parseFloat(formData.bruno_uyu) || null,
        bruno_usd: parseFloat(formData.bruno_usd) || null
      };

      if (editMode) {
        await axiosClient.patch(`/api/operaciones/${editMode.id}`, dataToSend);
        toast.success('✅ Distribución actualizada correctamente');
      } else {
        await axiosClient.post('/api/operaciones/distribucion', dataToSend);
        toast.success('✅ Distribución registrada correctamente');
      }
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
        localidad: 'Montevideo',
        tipo_cambio: '',
        descripcion: '',
        agustina_uyu: '',
        agustina_usd: '',
        viviana_uyu: '',
        viviana_usd: '',
        gonzalo_uyu: '',
        gonzalo_usd: '',
        pancho_uyu: '',
        pancho_usd: '',
        bruno_uyu: '',
        bruno_usd: ''
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
      title={editMode ? "Editar Distribución" : "Registrar Distribución"}
      submitLabel={editMode ? "Actualizar" : "Guardar"}
      onSubmit={handleSubmitInterno}
      isLoading={localLoading}
      size="max-w-2xl"
      borderColor="border-blue-500"
    >
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">Fecha</label>
          <input
            type="date"
            required
            value={formData.fecha}
            max={new Date().toISOString().split('T')[0]}
            onChange={(e) => setFormData({...formData, fecha: e.target.value})}
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">Localidad</label>
          <select
            value={formData.localidad}
            onChange={(e) => setFormData({...formData, localidad: e.target.value})}
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
          >
            <option value="Montevideo">Montevideo</option>
            <option value="Mercedes">Mercedes</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">T.C.</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={formData.tipo_cambio}
            onChange={(e) => setFormData({...formData, tipo_cambio: e.target.value})}
            className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
          />
        </div>
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">Montos por Socio</label>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-xs font-semibold text-gray-600 dark:text-gray-300">Socio</div>
          <div className="text-xs font-semibold text-gray-600 dark:text-gray-300">UYU</div>
          <div className="text-xs font-semibold text-gray-600 dark:text-gray-300">USD</div>
          
          <div className="text-xs py-1 dark:text-gray-200">Agustina</div>
          <input type="number" step="0.01" min="0" value={formData.agustina_uyu} onChange={(e) => setFormData({...formData, agustina_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.agustina_usd} onChange={(e) => setFormData({...formData, agustina_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1 dark:text-gray-200">Viviana</div>
          <input type="number" step="0.01" min="0" value={formData.viviana_uyu} onChange={(e) => setFormData({...formData, viviana_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.viviana_usd} onChange={(e) => setFormData({...formData, viviana_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1 dark:text-gray-200">Gonzalo</div>
          <input type="number" step="0.01" min="0" value={formData.gonzalo_uyu} onChange={(e) => setFormData({...formData, gonzalo_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.gonzalo_usd} onChange={(e) => setFormData({...formData, gonzalo_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1 dark:text-gray-200">Pancho</div>
          <input type="number" step="0.01" min="0" value={formData.pancho_uyu} onChange={(e) => setFormData({...formData, pancho_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.pancho_usd} onChange={(e) => setFormData({...formData, pancho_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1 dark:text-gray-200">Bruno</div>
          <input type="number" step="0.01" min="0" value={formData.bruno_uyu} onChange={(e) => setFormData({...formData, bruno_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.bruno_usd} onChange={(e) => setFormData({...formData, bruno_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
        </div>
      </div>

      <div className="mb-2">
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Descripción</label>
        <textarea
          value={formData.descripcion}
          onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
          className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
          rows="2"
          placeholder="Opcional"
        />
      </div>
    </ModalBase>
  );
}

export default ModalDistribucion;

