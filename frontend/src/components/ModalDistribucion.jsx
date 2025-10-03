import { useState, useEffect } from 'react';
import axios from 'axios';
import ModalBase from './shared/ModalBase';

function ModalDistribucion({ isOpen, onClose, onSuccess, setLoading }) {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
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

  const handleSubmitInterno = async () => {
    setLocalLoading(true);
    if (setLoading) setLoading(true);

    try {
      const dataToSend = {
        fecha: formData.fecha,
        descripcion: formData.descripcion || null,
        distribuciones: [
          { socio: 'Agustina', monto_uyu: parseFloat(formData.agustina_uyu) || 0, monto_usd: parseFloat(formData.agustina_usd) || 0 },
          { socio: 'Viviana', monto_uyu: parseFloat(formData.viviana_uyu) || 0, monto_usd: parseFloat(formData.viviana_usd) || 0 },
          { socio: 'Gonzalo', monto_uyu: parseFloat(formData.gonzalo_uyu) || 0, monto_usd: parseFloat(formData.gonzalo_usd) || 0 },
          { socio: 'Pancho', monto_uyu: parseFloat(formData.pancho_uyu) || 0, monto_usd: parseFloat(formData.pancho_usd) || 0 },
          { socio: 'Bruno', monto_uyu: parseFloat(formData.bruno_uyu) || 0, monto_usd: parseFloat(formData.bruno_usd) || 0 }
        ]
      };

      await axios.post('http://localhost:8000/api/operaciones/distribucion', dataToSend);
      
      onSuccess();
      onClose();
      
      setFormData({
        fecha: new Date().toISOString().split('T')[0],
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
      title="Registrar Distribución"
      onSubmit={handleSubmitInterno}
      isLoading={localLoading}
      size="max-w-2xl"
    >
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-700 mb-1">Fecha</label>
        <input
          type="date"
          required
          value={formData.fecha}
          max={new Date().toISOString().split('T')[0]}
          onChange={(e) => setFormData({...formData, fecha: e.target.value})}
          className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
        />
      </div>

      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-2">Montos por Socio</label>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-xs font-semibold text-gray-600">Socio</div>
          <div className="text-xs font-semibold text-gray-600">UYU</div>
          <div className="text-xs font-semibold text-gray-600">USD</div>
          
          <div className="text-xs py-1">Agustina</div>
          <input type="number" step="0.01" min="0" value={formData.agustina_uyu} onChange={(e) => setFormData({...formData, agustina_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.agustina_usd} onChange={(e) => setFormData({...formData, agustina_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1">Viviana</div>
          <input type="number" step="0.01" min="0" value={formData.viviana_uyu} onChange={(e) => setFormData({...formData, viviana_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.viviana_usd} onChange={(e) => setFormData({...formData, viviana_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1">Gonzalo</div>
          <input type="number" step="0.01" min="0" value={formData.gonzalo_uyu} onChange={(e) => setFormData({...formData, gonzalo_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.gonzalo_usd} onChange={(e) => setFormData({...formData, gonzalo_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1">Pancho</div>
          <input type="number" step="0.01" min="0" value={formData.pancho_uyu} onChange={(e) => setFormData({...formData, pancho_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.pancho_usd} onChange={(e) => setFormData({...formData, pancho_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          
          <div className="text-xs py-1">Bruno</div>
          <input type="number" step="0.01" min="0" value={formData.bruno_uyu} onChange={(e) => setFormData({...formData, bruno_uyu: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
          <input type="number" step="0.01" min="0" value={formData.bruno_usd} onChange={(e) => setFormData({...formData, bruno_usd: e.target.value})} className="px-1 py-1 border rounded text-xs" placeholder="0.00" />
        </div>
      </div>

      <div className="mb-2">
        <label className="block text-xs font-medium text-gray-700">Descripción</label>
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

