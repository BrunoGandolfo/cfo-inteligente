import PropTypes from 'prop-types';
import Modal from '../ui/Modal';
import { formatDateTime, deriveTipoCambio } from '../../utils/formatters';

export function OperationDetails({ open, onClose, op }) {
  if (!op) return null;
  const AREAS_MAP = {
    'd3aff49c-748c-4d1d-bc47-cdda1cfb913d': 'Jurídica',
    '53ba7821-8836-4e74-ad56-a288d290881d': 'Notarial',
    '14700c01-3b3d-49c6-8e2e-f3ebded1b1bb': 'Contable',
    '11c64c64-c7f6-4e85-9c26-b577c3d7a5b7': 'Recuperación',
    'b11006d3-6cfc-4766-9201-ab56274401a6': 'Gastos Generales',
    '651dfb5c-15d8-41e2-8339-785b137f44f2': 'Otros'
  };
  const tc = deriveTipoCambio(op);
  const areaNombre = AREAS_MAP[op.area_id] || 'Sin área';
  return (
    <Modal open={open} onClose={onClose} title="Detalle de Operación">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div><p className="text-sm text-gray-500">Fecha</p><p className="font-medium">{formatDateTime(op.fecha)}</p></div>
        <div><p className="text-sm text-gray-500">Tipo</p><p className="font-medium">{(op.tipo || op.tipo_operacion || '').toUpperCase()}</p></div>
        <div><p className="text-sm text-gray-500">Área</p><p className="font-medium">{areaNombre}</p></div>
        <div><p className="text-sm text-gray-500">Localidad</p><p className="font-medium">{op.localidad || 'No especificada'}</p></div>
        <div><p className="text-sm text-gray-500">Cliente</p><p className="font-medium">{op.cliente || '-'}</p></div>
        <div><p className="text-sm text-gray-500">Proveedor</p><p className="font-medium">{op.proveedor || '-'}</p></div>
      </div>
      <div className="bg-gray-50 dark:bg-slate-900 rounded-lg p-4 mb-6">
        <h5 className="font-semibold mb-3">Información financiera</h5>
        <div className="grid grid-cols-2 gap-4">
          <div><p className="text-sm text-gray-500">Monto UYU</p><p className="font-medium">{op.monto_uyu?.toLocaleString('es-UY')}</p></div>
          <div><p className="text-sm text-gray-500">Monto USD</p><p className="font-medium">{op.monto_usd?.toLocaleString('es-UY')}</p></div>
          <div><p className="text-sm text-gray-500">Tipo de cambio</p><p className="font-medium">{tc ?? 'N/A'}</p></div>
          <div>
            <p className="text-sm text-gray-500">Descripción</p>
            <p className="font-medium">{op.descripcion || 'Sin descripción'}</p>
          </div>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <button onClick={onClose} className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md">Cerrar</button>
      </div>
    </Modal>
  );
}
OperationDetails.propTypes = { open: PropTypes.bool, onClose: PropTypes.func, op: PropTypes.object };
export default OperationDetails;


