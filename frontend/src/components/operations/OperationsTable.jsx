import PropTypes from 'prop-types';
import { useOperations } from '../../hooks/useOperations';
import OperationRow from './OperationRow';
import Card from '../ui/Card';

export function OperationsTable({ refresh, onOpenDetails, onEdit }) {
  const { operacionesAll: operaciones, loading, anular } = useOperations(refresh);
  
  // 🔍 DIAGNÓSTICO OperationsTable
  
  return (
    <section className="px-6 mb-8">
      <Card className="overflow-hidden">
        <div className="px-6 py-3 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">Operaciones</h3>
        </div>
        {loading ? (
          <div className="p-6">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-surface-alt rounded w-1/3" />
              <div className="h-10 bg-surface rounded" />
              <div className="h-10 bg-surface rounded" />
              <div className="h-10 bg-surface rounded" />
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="sticky top-0 bg-surface">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase">Tercero</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-text-secondary uppercase">Monto</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-text-secondary uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-surface divide-y divide-border">
                {operaciones.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-text-secondary">
                      No hay operaciones en el período seleccionado
                    </td>
                  </tr>
                ) : (
                  operaciones.map((op) => (
                    <OperationRow key={op.id} op={op} onSelect={onOpenDetails} onEdit={onEdit} onDelete={anular} />
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </section>
  );
}
OperationsTable.propTypes = { refresh: PropTypes.number, onOpenDetails: PropTypes.func, onEdit: PropTypes.func };
export default OperationsTable;


