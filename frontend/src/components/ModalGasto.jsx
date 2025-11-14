import { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import ModalBase from './shared/ModalBase';

function ModalGasto({ isOpen, onClose, onSuccess, setLoading, editMode }) {
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
  
  // Áreas productivas + Gastos Generales (área residual para gastos)
  // "Otros" es SOLO para INGRESOS, no para GASTOS
  const [areas] = useState([
    { id: 'd3aff49c-748c-4d1d-bc47-cdda1cfb913d', nombre: 'Jurídica' },
    { id: '53ba7821-8836-4e74-ad56-a288d290881d', nombre: 'Notarial' },
    { id: '14700c01-3b3d-49c6-8e2e-f3ebded1b1bb', nombre: 'Contable' },
    { id: '11c64c64-c7f6-4e85-9c26-b577c3d7a5b7', nombre: 'Recuperación' },
    { id: 'b11006d3-6cfc-4766-9201-ab56274401a6', nombre: 'Gastos Generales' }
  ]);
  
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (editMode) {
        setFormData({
          fecha: editMode.fecha,
          proveedor: editMode.proveedor || '',
          proveedor_telefono: '',
          area_id: editMode.area?.id || editMode.area_id || '',
          localidad: editMode.localidad || 'Montevideo',
          monto_original: editMode.monto_original?.toString() || '',
          moneda_original: editMode.moneda_original || 'UYU',
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
        proveedor: formData.proveedor || null,
        proveedor_telefono: formData.proveedor_telefono || null,
        area_id: formData.area_id,
        localidad: formData.localidad,
        monto_original: parseFloat(formData.monto_original),
        moneda_original: formData.moneda_original,
        tipo_cambio: parseFloat(formData.tipo_cambio) || 40.50,
        descripcion: formData.descripcion || null
      };

      if (editMode) {
        await axios.patch(`http://localhost:8000/api/operaciones/${editMode.id}`, dataToSend);
        toast.success('✅ Gasto actualizado correctamente');
      } else {
        await axios.post('http://localhost:8000/api/operaciones/gasto', dataToSend);
        toast.success('✅ Gasto registrado correctamente');
      }
      
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
    } finally {
      setLocalLoading(false);
      if (setLoading) setLoading(false);
    }
  };

  return (
    <ModalBase
      isOpen={isOpen}
      onClose={onClose}
      title={editMode ? "Editar Gasto" : "Registrar Gasto"}
      submitLabel={editMode ? "Actualizar" : "Guardar"}
      onSubmit={handleSubmitInterno}
      isLoading={localLoading}
      size="max-w-2xl"
      borderColor="border-red-500"
    >
      <div className="grid grid-cols-3 gap-2 mb-2">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Fecha</label>
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
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Área *</label>
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
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Local</label>
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

      <div className="mb-2">
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Proveedor *</label>
        <input
          type="text"
          required
          value={formData.proveedor}
          onChange={(e) => setFormData({...formData, proveedor: e.target.value})}
          className="w-full px-1 py-1 border border-gray-300 rounded text-xs"
          placeholder="Nombre del proveedor"
        />
      </div>

      <div className="grid grid-cols-3 gap-2 mb-2">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Moneda</label>
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
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Monto *</label>
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
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">T.C.</label>
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

      <div className="mb-2">
        <label className="block text-xs font-medium text-gray-700 dark:text-gray-200">Descripción</label>
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

export default ModalGasto;

