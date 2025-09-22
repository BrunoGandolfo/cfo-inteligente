import PropTypes from 'prop-types';
import { Badge } from '../ui/Badge';
import { formatDateShort, formatMoneySmart } from '../../utils/formatters';

export function OperationRow({ op, onSelect, onCancel }) {
  const tipo = (op.tipo || op.tipo_operacion || '').toUpperCase();
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer" onClick={() => onSelect(op)}>
      <td className="px-4 py-3 text-sm text-gray-900 dark:text-slate-100">{formatDateShort(op.fecha)}</td>
      <td className="px-4 py-3"><Badge tipo={tipo} /></td>
      <td className="px-4 py-3 text-sm text-gray-900 dark:text-slate-100">{op.cliente || op.proveedor || '-'}</td>
      <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900 dark:text-slate-100">{formatMoneySmart(op)}</td>
      <td className="px-4 py-3 text-center">
        <button className="text-red-600 hover:text-red-800 text-sm" onClick={(e) => { e.stopPropagation(); onCancel(op.id); }}>
          Anular
        </button>
      </td>
    </tr>
  );
}
OperationRow.propTypes = { op: PropTypes.object, onSelect: PropTypes.func, onCancel: PropTypes.func };
export default OperationRow;


