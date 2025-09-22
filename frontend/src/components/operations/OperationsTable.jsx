import PropTypes from 'prop-types';
import { useOperations } from '../../hooks/useOperations';
import OperationRow from './OperationRow';
import Card from '../ui/Card';

export function OperationsTable({ refresh, onOpenDetails }) {
  const { operaciones, loading, anular } = useOperations(refresh);
  return (
    <section className="px-6 mb-8">
      <Card className="overflow-hidden">
        <div className="px-6 py-3 border-b border-gray-200 dark:border-slate-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Operaciones</h3>
        </div>
        {loading ? (
          <div className="p-6 text-center text-gray-500 dark:text-slate-300">Cargando operaciones...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50 dark:bg-slate-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tercero</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Monto</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-slate-900 divide-y divide-gray-200 dark:divide-slate-800">
                {operaciones.length === 0 ? (
                  <tr><td colSpan="5" className="px-6 py-8 text-center text-gray-500 dark:text-slate-300">No hay operaciones registradas</td></tr>
                ) : (
                  operaciones.map((op) => (
                    <OperationRow key={op.id} op={op} onSelect={onOpenDetails} onCancel={anular} />
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
OperationsTable.propTypes = { refresh: PropTypes.number, onOpenDetails: PropTypes.func };
export default OperationsTable;


