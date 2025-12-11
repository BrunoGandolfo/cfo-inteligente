import { useState } from 'react';
import PropTypes from 'prop-types';
import { X, FileText } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import clsx from 'clsx';
import toast from 'react-hot-toast';
import { useMetrics } from '../../hooks/useMetrics';
import OperationsTable from './OperationsTable';
import OperationDetails from './OperationDetails';
import ModalIngreso from '../ModalIngreso';
import ModalGasto from '../ModalGasto';
import ModalRetiro from '../ModalRetiro';
import ModalDistribucion from '../ModalDistribucion';

export function OperationsPanel({ isOpen, onClose }) {
  const { refreshKey } = useMetrics();
  const [detailOp, setDetailOp] = useState(null);
  const [editOp, setEditOp] = useState(null);
  
  const handleEdit = (op) => {
    setEditOp(op);
  };
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay para móvil */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 z-40 lg:hidden"
          />

          {/* Panel */}
          <motion.aside
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={clsx(
              'fixed right-0 top-16 h-[calc(100vh-4rem)] w-full sm:w-[500px] lg:w-[600px]',
              'bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800',
              'shadow-2xl z-50 flex flex-col'
            )}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">Operaciones</h2>
                  <p className="text-xs text-gray-500 dark:text-slate-400">Gestión de transacciones</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
                aria-label="Cerrar panel"
              >
                <X className="w-5 h-5 text-gray-600 dark:text-slate-400" />
              </button>
            </div>

            {/* Body con tabla */}
            <div className="flex-1 overflow-y-auto">
              <OperationsTable 
                refresh={refreshKey} 
                onOpenDetails={(op) => setDetailOp(op)}
                onEdit={handleEdit}
              />
            </div>

            {/* Modal de detalles */}
            <OperationDetails open={!!detailOp} onClose={() => setDetailOp(null)} op={detailOp} />
            
            {/* Modales de edición */}
            {editOp && editOp.tipo_operacion === 'ingreso' && (
              <ModalIngreso 
                isOpen={true}
                onClose={() => setEditOp(null)}
                onSuccess={() => setEditOp(null)}
                editMode={editOp}
              />
            )}
            {editOp && editOp.tipo_operacion === 'gasto' && (
              <ModalGasto 
                isOpen={true}
                onClose={() => setEditOp(null)}
                onSuccess={() => setEditOp(null)}
                editMode={editOp}
              />
            )}
            {editOp && editOp.tipo_operacion === 'retiro' && (
              <ModalRetiro 
                isOpen={true}
                onClose={() => setEditOp(null)}
                onSuccess={() => setEditOp(null)}
                editMode={editOp}
              />
            )}
            {editOp && editOp.tipo_operacion === 'distribucion' && (
              <ModalDistribucion 
                isOpen={true}
                onClose={() => setEditOp(null)}
                onSuccess={() => setEditOp(null)}
                editMode={editOp}
              />
            )}
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

OperationsPanel.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired
};

export default OperationsPanel;

