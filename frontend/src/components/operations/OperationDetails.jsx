import PropTypes from 'prop-types';
import Modal from '../ui/Modal';
import { formatDateTime, deriveTipoCambio } from '../../utils/formatters';

export function OperationDetails({ open, onClose, op }) {
  if (!op) return null;
  const tc = deriveTipoCambio(op);
  return (
    <Modal open={open} onClose={onClose} title="Detalle de Operación">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div><p className="text-sm text-gray-500">Fecha</p><p className="font-medium">{formatDateTime(op.fecha)}</p></div>
        <div><p className="text-sm text-gray-500">Tipo</p><p className="font-medium">{(op.tipo || op.tipo_operacion || '').toUpperCase()}</p></div>
        <div><p className="text-sm text-gray-500">Cliente</p><p className="font-medium">{op.cliente || '-'}</p></div>
        <div><p className="text-sm text-gray-500">Proveedor</p><p className="font-medium">{op.proveedor || '-'}</p></div>
      </div>
      <div className="bg-gray-50 dark:bg-slate-900 rounded-lg p-4 mb-6">
        <h5 className="font-semibold mb-3">Información financiera</h5>
        <div className="grid grid-cols-2 gap-4">
          <div><p className="text-sm text-gray-500">Monto UYU</p><p className="font-medium">{op.monto_uyu?.toLocaleString('es-UY')}</p></div>
          <div><p className="text-sm text-gray-500">Monto USD</p><p className="font-medium">{op.monto_usd?.toLocaleString('es-UY')}</p></div>
          <div><p className="text-sm text-gray-500">Tipo de cambio</p><p className="font-medium">{tc ?? 'N/A'}</p></div>
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


