import PropTypes from 'prop-types';
import { Badge } from '../ui/Badge';
import { formatDateShort, formatMoneySmart } from '../../utils/formatters';

export function OperationRow({ op, onSelect, onEdit, onDelete }) {
  const tipo = (op.tipo || op.tipo_operacion || '').toUpperCase();
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-slate-800 cursor-pointer" onClick={() => onSelect(op)}>
      <td className="px-4 py-3 text-sm text-gray-900 dark:text-slate-100">{formatDateShort(op.fecha)}</td>
      <td className="px-4 py-3"><Badge tipo={tipo} /></td>
      <td className="px-4 py-3 text-sm text-gray-900 dark:text-slate-100">{op.cliente || op.proveedor || '-'}</td>
      <td className="px-4 py-3 text-sm text-right font-semibold text-gray-900 dark:text-slate-100">{formatMoneySmart(op)}</td>
      <td className="px-4 py-3 text-center space-x-2">
        <button className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium" onClick={(e) => { e.stopPropagation(); onEdit(op); }}>
          Editar
        </button>
        <button className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 text-sm font-medium" onClick={(e) => { e.stopPropagation(); onDelete(op.id); }}>
          Eliminar
        </button>
      </td>
    </tr>
  );
}
OperationRow.propTypes = { op: PropTypes.object, onSelect: PropTypes.func, onEdit: PropTypes.func, onDelete: PropTypes.func };
export default OperationRow;


